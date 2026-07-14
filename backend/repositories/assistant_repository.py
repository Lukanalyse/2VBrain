import re
import struct
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from models.assistant_index import AssistantChunk, AssistantDocument, AssistantProjectDocument


@dataclass(frozen=True)
class AssistantChunkInput:
    ordinal: int
    heading: str
    page_number: int | None
    content: str
    embedding: list[float]


@dataclass(frozen=True)
class AssistantChunkRecord:
    chunk_id: int
    content: str
    heading: str
    page_number: int | None
    embedding: tuple[float, ...]
    object_id: str
    object_type: str
    object_title: str
    object_subtitle: str
    object_markdown_path: str
    source_kind: str
    source_title: str
    source_path: str


class AssistantRepository:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._ensure_fts()

    def get_current_document(
        self, source_key: str, content_hash: str, embedding_model: str
    ) -> AssistantDocument | None:
        document = self._db.scalar(
            select(AssistantDocument).where(AssistantDocument.source_key == source_key)
        )
        if document is None:
            return None
        chunk_count = self._db.scalar(
            select(func.count(AssistantChunk.id)).where(AssistantChunk.document_id == document.id)
        )
        if (
            document.content_hash != content_hash
            or document.embedding_model != embedding_model
            or not chunk_count
        ):
            return None
        return document

    def replace_document(
        self,
        *,
        source_key: str,
        object_id: str,
        object_type: str,
        object_title: str,
        object_subtitle: str,
        object_markdown_path: str,
        source_kind: str,
        source_title: str,
        source_path: str,
        content_hash: str,
        embedding_model: str,
        chunks: list[AssistantChunkInput],
    ) -> AssistantDocument:
        document = self._db.scalar(
            select(AssistantDocument).where(AssistantDocument.source_key == source_key)
        )
        if document is None:
            document = AssistantDocument(source_key=source_key)
            self._db.add(document)
        else:
            chunk_ids = self._db.scalars(
                select(AssistantChunk.id).where(AssistantChunk.document_id == document.id)
            ).all()
            for chunk_id in chunk_ids:
                self._db.execute(
                    text("DELETE FROM assistant_chunks_fts WHERE rowid = :chunk_id"),
                    {"chunk_id": chunk_id},
                )
            self._db.execute(
                delete(AssistantChunk).where(AssistantChunk.document_id == document.id)
            )

        document.object_id = object_id
        document.object_type = object_type
        document.object_title = object_title
        document.object_subtitle = object_subtitle
        document.object_markdown_path = object_markdown_path
        document.source_kind = source_kind
        document.source_title = source_title
        document.source_path = source_path
        document.content_hash = content_hash
        document.embedding_model = embedding_model
        document.indexed_at = datetime.now(UTC)
        self._db.flush()

        for item in chunks:
            chunk = AssistantChunk(
                document_id=document.id,
                ordinal=item.ordinal,
                heading=item.heading,
                page_number=item.page_number,
                content=item.content,
                embedding=self.pack_embedding(item.embedding),
                embedding_dimensions=len(item.embedding),
            )
            self._db.add(chunk)
            self._db.flush()
            self._db.execute(
                text(
                    "INSERT INTO assistant_chunks_fts(rowid, chunk_id, content) "
                    "VALUES (:rowid, :chunk_id, :content)"
                ),
                {"rowid": chunk.id, "chunk_id": chunk.id, "content": chunk.content},
            )

        self._db.commit()
        self._db.refresh(document)
        return document

    def sync_project_documents(self, project_id: str, document_ids: set[int]) -> None:
        existing = {
            mapping.document_id: mapping
            for mapping in self._db.scalars(
                select(AssistantProjectDocument).where(
                    AssistantProjectDocument.project_id == project_id
                )
            ).all()
        }
        for document_id, mapping in existing.items():
            if document_id not in document_ids:
                self._db.delete(mapping)
        for document_id in document_ids - set(existing):
            self._db.add(AssistantProjectDocument(project_id=project_id, document_id=document_id))
        self._db.commit()

    def project_counts(self, project_id: str) -> tuple[int, int]:
        document_count = self._db.scalar(
            select(func.count(AssistantProjectDocument.id)).where(
                AssistantProjectDocument.project_id == project_id
            )
        )
        chunk_count = self._db.scalar(
            select(func.count(AssistantChunk.id))
            .join(
                AssistantProjectDocument,
                AssistantProjectDocument.document_id == AssistantChunk.document_id,
            )
            .where(AssistantProjectDocument.project_id == project_id)
        )
        return int(document_count or 0), int(chunk_count or 0)

    def lexical_chunks(
        self, project_id: str, query: str, limit: int = 24
    ) -> list[AssistantChunkRecord]:
        fts_query = self._fts_query(query)
        if not fts_query:
            return []
        rows = self._db.execute(
            text(
                "SELECT assistant_chunks.rowid AS chunk_id "
                "FROM assistant_chunks_fts "
                "JOIN assistant_chunks "
                "  ON assistant_chunks.id = assistant_chunks_fts.rowid "
                "JOIN assistant_project_documents "
                "  ON assistant_project_documents.document_id = assistant_chunks.document_id "
                "WHERE assistant_chunks_fts MATCH :query "
                "  AND assistant_project_documents.project_id = :project_id "
                "ORDER BY bm25(assistant_chunks_fts) "
                "LIMIT :limit"
            ),
            {"query": fts_query, "project_id": project_id, "limit": limit},
        ).all()
        return self._records_by_ids([int(row.chunk_id) for row in rows])

    def project_chunks(self, project_id: str) -> list[AssistantChunkRecord]:
        rows = self._db.execute(
            select(AssistantChunk, AssistantDocument)
            .join(AssistantDocument, AssistantDocument.id == AssistantChunk.document_id)
            .join(
                AssistantProjectDocument,
                AssistantProjectDocument.document_id == AssistantDocument.id,
            )
            .where(AssistantProjectDocument.project_id == project_id)
            .order_by(AssistantChunk.id)
        ).all()
        return [self._record(chunk, document) for chunk, document in rows]

    def _records_by_ids(self, chunk_ids: list[int]) -> list[AssistantChunkRecord]:
        if not chunk_ids:
            return []
        rows = self._db.execute(
            select(AssistantChunk, AssistantDocument)
            .join(AssistantDocument, AssistantDocument.id == AssistantChunk.document_id)
            .where(AssistantChunk.id.in_(chunk_ids))
        ).all()
        by_id = {chunk.id: self._record(chunk, document) for chunk, document in rows}
        return [by_id[chunk_id] for chunk_id in chunk_ids if chunk_id in by_id]

    def _record(self, chunk: AssistantChunk, document: AssistantDocument) -> AssistantChunkRecord:
        return AssistantChunkRecord(
            chunk_id=chunk.id,
            content=chunk.content,
            heading=chunk.heading,
            page_number=chunk.page_number,
            embedding=self.unpack_embedding(chunk.embedding, chunk.embedding_dimensions),
            object_id=document.object_id,
            object_type=document.object_type,
            object_title=document.object_title,
            object_subtitle=document.object_subtitle,
            object_markdown_path=document.object_markdown_path,
            source_kind=document.source_kind,
            source_title=document.source_title,
            source_path=document.source_path,
        )

    def _ensure_fts(self) -> None:
        self._db.execute(
            text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS assistant_chunks_fts "
                "USING fts5(chunk_id UNINDEXED, content, "
                "tokenize='unicode61 remove_diacritics 2')"
            )
        )
        self._db.commit()

    def _fts_query(self, value: str) -> str:
        tokens = re.findall(r"[^\W_]+", value.lower(), flags=re.UNICODE)
        return " OR ".join(f'"{token}"' for token in tokens[:16])

    @staticmethod
    def pack_embedding(values: list[float]) -> bytes:
        return struct.pack(f"<{len(values)}f", *values)

    @staticmethod
    def unpack_embedding(payload: bytes, dimensions: int) -> tuple[float, ...]:
        if dimensions <= 0 or len(payload) != dimensions * 4:
            return ()
        return struct.unpack(f"<{dimensions}f", payload)
