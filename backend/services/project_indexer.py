import hashlib
import json
import re
from dataclasses import dataclass

import yaml
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from repositories.assistant_repository import AssistantChunkInput, AssistantRepository
from schemas.assistant import AssistantConfigResponse, ProjectIndexStatus
from services.ollama_client import OllamaClient
from services.project_corpus import ProjectCorpusResolver, ProjectSource


@dataclass(frozen=True)
class ExtractedChunk:
    heading: str
    page_number: int | None
    content: str


class ProjectIndexer:
    def __init__(
        self,
        *,
        corpus_resolver: ProjectCorpusResolver,
        repository: AssistantRepository,
        ollama: OllamaClient,
    ) -> None:
        self._corpus_resolver = corpus_resolver
        self._repository = repository
        self._ollama = ollama

    def status(self, project_id: str, config: AssistantConfigResponse) -> ProjectIndexStatus:
        document_count, chunk_count = self._repository.project_counts(project_id)
        return ProjectIndexStatus(
            project_id=project_id,
            ready=chunk_count > 0,
            document_count=document_count,
            chunk_count=chunk_count,
            embedding_model=config.embedding_model,
        )

    def index(self, project_id: str, config: AssistantConfigResponse) -> ProjectIndexStatus:
        sources = self._corpus_resolver.resolve(project_id)
        document_ids: set[int] = set()
        updated_documents = 0
        errors: list[str] = []

        for source in sources:
            try:
                content_hash = self._source_hash(source)
                current = self._repository.get_current_document(
                    source.source_key, content_hash, config.embedding_model
                )
                if current is not None:
                    document_ids.add(current.id)
                    continue
                chunks = self._extract(source)
            except (OSError, PdfReadError, ValueError) as error:
                errors.append(f"{source.source_title}: {error}")
                continue
            if not chunks:
                continue

            embedding_inputs = [
                f"{source.source_title}\n{chunk.heading}\n{chunk.content}" for chunk in chunks
            ]
            embeddings = self._embed_batches(embedding_inputs, config.embedding_model)
            indexed_chunks = [
                AssistantChunkInput(
                    ordinal=index,
                    heading=chunk.heading,
                    page_number=chunk.page_number,
                    content=chunk.content,
                    embedding=embeddings[index],
                )
                for index, chunk in enumerate(chunks)
            ]
            document = self._repository.replace_document(
                source_key=source.source_key,
                object_id=source.object.id,
                object_type=source.object.type.value,
                object_title=source.object.title,
                object_subtitle=source.object.subtitle,
                object_markdown_path=source.object.markdown_path,
                source_kind=source.source_kind,
                source_title=source.source_title,
                source_path=str(source.path),
                content_hash=content_hash,
                embedding_model=config.embedding_model,
                chunks=indexed_chunks,
            )
            document_ids.add(document.id)
            updated_documents += 1

        self._repository.sync_project_documents(project_id, document_ids)
        document_count, chunk_count = self._repository.project_counts(project_id)
        return ProjectIndexStatus(
            project_id=project_id,
            ready=chunk_count > 0,
            document_count=document_count,
            chunk_count=chunk_count,
            embedding_model=config.embedding_model,
            updated_documents=updated_documents,
            errors=errors,
        )

    def _extract(self, source: ProjectSource) -> list[ExtractedChunk]:
        if source.source_kind == "pdf":
            return self._extract_pdf(source)
        return self._extract_markdown(source)

    def _extract_markdown(self, source: ProjectSource) -> list[ExtractedChunk]:
        content = source.path.read_text(encoding="utf-8")
        metadata, body = self._frontmatter(content)
        chunks: list[ExtractedChunk] = []
        if metadata:
            metadata_text = "\n".join(
                f"{key}: {self._metadata_value(value)}"
                for key, value in metadata.items()
                if value not in (None, "", [], {})
            )
            chunks.extend(self._chunk_section("Metadata", metadata_text))

        heading = "Document"
        lines: list[str] = []

        def flush() -> None:
            text = "\n".join(lines).strip()
            if text:
                chunks.extend(self._chunk_section(heading, text))

        for line in body.splitlines():
            match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
            if match:
                flush()
                heading = match.group(1).strip()
                lines = []
            else:
                lines.append(line)
        flush()
        return chunks

    def _extract_pdf(self, source: ProjectSource) -> list[ExtractedChunk]:
        reader = PdfReader(str(source.path))
        chunks: list[ExtractedChunk] = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            for content in self._split_text(text):
                chunks.append(
                    ExtractedChunk(
                        heading=f"Page {page_number}",
                        page_number=page_number,
                        content=content,
                    )
                )
        return chunks

    def _frontmatter(self, content: str) -> tuple[dict[str, object], str]:
        match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", content, re.DOTALL)
        if not match:
            return {}, content
        data = yaml.safe_load(match.group(1)) or {}
        metadata = data if isinstance(data, dict) else {}
        return metadata, content[match.end() :]

    def _metadata_value(self, value: object) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        return str(value)

    def _chunk_section(self, heading: str, content: str) -> list[ExtractedChunk]:
        return [
            ExtractedChunk(heading=heading, page_number=None, content=chunk)
            for chunk in self._split_text(content)
        ]

    def _split_text(self, content: str, max_chars: int = 1800) -> list[str]:
        compact = re.sub(r"[ \t]+", " ", content).strip()
        if not compact:
            return []
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", compact) if part.strip()]
        chunks: list[str] = []
        current = ""
        for paragraph in paragraphs:
            parts = self._split_long_paragraph(paragraph, max_chars)
            for part in parts:
                candidate = f"{current}\n\n{part}".strip() if current else part
                if len(candidate) <= max_chars:
                    current = candidate
                    continue
                if current:
                    chunks.append(current)
                current = part
        if current:
            chunks.append(current)
        return chunks

    def _split_long_paragraph(self, paragraph: str, max_chars: int) -> list[str]:
        if len(paragraph) <= max_chars:
            return [paragraph]
        words = paragraph.split()
        parts: list[str] = []
        current: list[str] = []
        length = 0
        for word in words:
            next_length = length + len(word) + (1 if current else 0)
            if current and next_length > max_chars:
                parts.append(" ".join(current))
                current = []
                length = 0
            current.append(word)
            length += len(word) + (1 if length else 0)
        if current:
            parts.append(" ".join(current))
        return parts

    def _embed_batches(self, texts: list[str], model: str) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), 24):
            embeddings.extend(self._ollama.embed(texts[start : start + 24], model))
        return embeddings

    def _source_hash(self, source: ProjectSource) -> str:
        digest = hashlib.sha256()
        with source.path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
