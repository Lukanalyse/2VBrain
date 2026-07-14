import json
import re
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import SpooledTemporaryFile

from core.settings import Settings
from repositories.library_repository import LibraryRepository
from schemas.library import DuplicateStrategy, PdfMetadataPreviewResponse
from services.paper_metadata_provider import BibliographicMetadata, PaperMetadataProvider
from services.pdf_metadata_extractor import PdfMetadataExtractor
from services.vault_manager import VaultManager


class LibraryImportError(Exception):
    pass


MAX_PDF_SIZE_BYTES = 100 * 1024 * 1024


class LibraryConflictError(Exception):
    def __init__(self, message: str, existing_item) -> None:
        super().__init__(message)
        self.existing_item = existing_item


@dataclass(frozen=True)
class IncomingDocument:
    filename: str
    file: SpooledTemporaryFile[bytes]
    content_type: str | None = None


class LibraryManager:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: LibraryRepository,
        vault_manager: VaultManager,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._vault_manager = vault_manager

    def list_items(self):
        return self._repository.list_items()

    def preview_pdf_metadata(self, document: IncomingDocument) -> PdfMetadataPreviewResponse:
        self._validate_pdf(document)
        try:
            extracted = PdfMetadataExtractor().extract(document.file)
        except Exception as error:
            raise LibraryImportError(
                "Unable to read PDF metadata. The file may be encrypted or malformed."
            ) from error

        local = BibliographicMetadata(
            title=extracted.title,
            authors=extracted.authors,
            journal=extracted.journal,
            conference=extracted.conference,
            year=extracted.year,
            doi=extracted.doi,
            abstract=extracted.abstract,
            keywords=extracted.keywords,
        )
        enriched = (
            PaperMetadataProvider().enrich(local)
            if self._settings.enable_online_metadata
            else local
        )

        return PdfMetadataPreviewResponse(
            title=enriched.title,
            authors=enriched.authors,
            journal=enriched.journal,
            conference=enriched.conference,
            year=enriched.year,
            doi=enriched.doi,
            abstract=enriched.abstract,
            keywords=enriched.keywords,
            publisher=enriched.publisher,
            source_url=enriched.source_url,
            metadata_source=enriched.metadata_source,
            metadata_confidence=enriched.metadata_confidence,
        )

    def import_pdf(
        self,
        document: IncomingDocument,
        duplicate_strategy: DuplicateStrategy = DuplicateStrategy.cancel,
        metadata: PdfMetadataPreviewResponse | None = None,
    ):
        self._validate_pdf(document)
        metadata = metadata or self.preview_pdf_metadata(document)

        existing_item = self._repository.get_by_original_filename(document.filename)
        if existing_item and duplicate_strategy == DuplicateStrategy.cancel:
            raise LibraryConflictError("This PDF has already been imported.", existing_item)

        vault_path = self._get_configured_vault_path()
        # The PDF and its note both live inside the Obsidian vault so the file
        # the user opens is the real vault file (visible in Obsidian and Finder),
        # not a copy under ./library. The vault is mounted at the same absolute
        # path in Docker, so this path is also valid on the host.
        vault_papers_dir = vault_path / "02 Library" / "Papers"
        vault_papers_dir.mkdir(parents=True, exist_ok=True)

        base_name = self._safe_stem(document.filename)
        target_stem = (
            base_name
            if duplicate_strategy == DuplicateStrategy.replace
            else self._available_stem(base_name, vault_papers_dir, vault_papers_dir)
        )
        pdf_path = vault_papers_dir / f"{target_stem}.pdf"
        markdown_path = vault_papers_dir / f"{target_stem}.md"

        self._copy_pdf(document, pdf_path)
        self._write_markdown_note(markdown_path, metadata)
        metadata_updated_at = datetime.now(UTC)

        if existing_item and duplicate_strategy == DuplicateStrategy.replace:
            return self._repository.replace_item(
                existing_item,
                filename=pdf_path.name,
                file_path=str(pdf_path),
                markdown_path=str(markdown_path),
                title=metadata.title or None,
                authors=metadata.authors or None,
                journal=metadata.journal or None,
                conference=metadata.conference or None,
                year=metadata.year,
                doi=metadata.doi or None,
                abstract=metadata.abstract or None,
                keywords=metadata.keywords or None,
                publisher=metadata.publisher or None,
                source_url=metadata.source_url or None,
                metadata_source=metadata.metadata_source or None,
                metadata_confidence=metadata.metadata_confidence or None,
                metadata_updated_at=metadata_updated_at,
                reading_progress=metadata.reading_progress,
                importance=metadata.importance or None,
                priority=metadata.priority or None,
                domain=metadata.domain or None,
                method=metadata.method or None,
                difficulty=metadata.difficulty or None,
                personal_tags=metadata.personal_tags or None,
                project_id=metadata.project_id or None,
            )

        return self._repository.create_item(
            filename=pdf_path.name,
            original_filename=document.filename,
            file_path=str(pdf_path),
            markdown_path=str(markdown_path),
            title=metadata.title or None,
            authors=metadata.authors or None,
            journal=metadata.journal or None,
            conference=metadata.conference or None,
            year=metadata.year,
            doi=metadata.doi or None,
            abstract=metadata.abstract or None,
            keywords=metadata.keywords or None,
            publisher=metadata.publisher or None,
            source_url=metadata.source_url or None,
            metadata_source=metadata.metadata_source or None,
            metadata_confidence=metadata.metadata_confidence or None,
            metadata_updated_at=metadata_updated_at,
            reading_progress=metadata.reading_progress,
            importance=metadata.importance or None,
            priority=metadata.priority or None,
            domain=metadata.domain or None,
            method=metadata.method or None,
            difficulty=metadata.difficulty or None,
            personal_tags=metadata.personal_tags or None,
            project_id=metadata.project_id or None,
        )

    def _get_configured_vault_path(self) -> Path:
        storage_status = self._vault_manager.get_storage_status()
        if not storage_status.is_configured or storage_status.vault_path is None:
            raise LibraryImportError("Configure a valid Obsidian vault before importing papers.")

        return storage_status.vault_path

    def _validate_pdf(self, document: IncomingDocument) -> None:
        if not document.filename.lower().endswith(".pdf"):
            raise LibraryImportError("Only PDF files can be imported.")

        current_position = document.file.tell()
        document.file.seek(0, 2)
        size = document.file.tell()
        if size > MAX_PDF_SIZE_BYTES:
            document.file.seek(current_position)
            raise LibraryImportError("PDF files larger than 100 MB cannot be imported.")
        document.file.seek(0)
        signature = document.file.read(5)
        document.file.seek(current_position)

        if signature != b"%PDF-":
            raise LibraryImportError("The selected file is not a valid PDF.")

    def _copy_pdf(self, document: IncomingDocument, destination: Path) -> None:
        document.file.seek(0)
        with destination.open("wb") as output_file:
            shutil.copyfileobj(document.file, output_file)

    def _write_markdown_note(self, destination: Path, metadata: PdfMetadataPreviewResponse) -> None:
        now = datetime.now(UTC).isoformat()
        destination.write_text(
            "---\n"
            f"title: {self._frontmatter_text(metadata.title)}\n"
            f"authors: {self._frontmatter_text(metadata.authors)}\n"
            f"journal: {self._frontmatter_text(metadata.journal)}\n"
            f"conference: {self._frontmatter_text(metadata.conference)}\n"
            f"year: {metadata.year or ''}\n"
            f"doi: {self._frontmatter_text(metadata.doi)}\n"
            f"keywords: {self._frontmatter_text(metadata.keywords)}\n"
            f"publisher: {self._frontmatter_text(metadata.publisher)}\n"
            f"source_url: {self._frontmatter_text(metadata.source_url)}\n"
            f"metadata_source: {self._frontmatter_text(metadata.metadata_source)}\n"
            f"metadata_confidence: {self._frontmatter_text(metadata.metadata_confidence)}\n"
            f"status: {self._frontmatter_text(metadata.reading_status)}\n"
            f"reading_progress: {metadata.reading_progress}\n"
            f"importance: {self._frontmatter_text(metadata.importance)}\n"
            f"priority: {self._frontmatter_text(metadata.priority)}\n"
            f"domain: {self._frontmatter_text(metadata.domain)}\n"
            f"method: {self._frontmatter_text(metadata.method)}\n"
            f"difficulty: {self._frontmatter_text(metadata.difficulty)}\n"
            f"tags: {self._frontmatter_text(metadata.personal_tags)}\n"
            f"project_id: {self._frontmatter_text(metadata.project_id)}\n"
            f"project: {self._frontmatter_text(self._project_label(metadata.project_id))}\n"
            "collection: inbox\n"
            f"created: {now}\n"
            f"updated: {now}\n"
            "---\n\n"
            "# Abstract\n\n"
            f"{metadata.abstract}\n\n"
            "# Reading Note\n\n"
            "## Research Question\n\n"
            "## Core Contribution\n\n"
            "## Method\n\n"
            "## Key Results\n\n"
            "## Evidence and Quotations\n\n"
            "## Limitations\n\n"
            "## Use in My Research\n\n"
            "## Open Questions\n\n"
            "# Related Papers\n\n"
            "# Related Concepts\n\n"
            "# Projects\n\n"
            f"{self._project_link(metadata.project_id)}\n\n"
            "# Literature Reviews\n\n"
            "# Brainstorm\n\n"
            "# References\n\n",
            encoding="utf-8",
        )

    def _frontmatter_text(self, value: str) -> str:
        value = value.strip()
        if not value:
            return ""
        return json.dumps(value, ensure_ascii=False)

    def _project_label(self, project_id: str) -> str:
        if not project_id.startswith("project:"):
            return ""
        return project_id.split(":", 1)[1]

    def _project_link(self, project_id: str) -> str:
        label = self._project_label(project_id)
        return f"- [[{label}]]" if label else ""

    def _safe_stem(self, filename: str) -> str:
        stem = Path(filename).stem.strip()
        cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", stem)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or "Untitled Paper"

    def _available_stem(self, base_name: str, pdf_dir: Path, markdown_dir: Path) -> str:
        candidate = base_name
        counter = 2

        while (pdf_dir / f"{candidate}.pdf").exists() or (
            markdown_dir / f"{candidate}.md"
        ).exists():
            candidate = f"{base_name} {counter}"
            counter += 1

        return candidate
