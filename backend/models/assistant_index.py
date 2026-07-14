from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class AssistantDocument(Base):
    __tablename__ = "assistant_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_key: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True, index=True)
    object_id: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    object_type: Mapped[str] = mapped_column(String(32), nullable=False)
    object_title: Mapped[str] = mapped_column(String(512), nullable=False)
    object_subtitle: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    object_markdown_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source_title: Mapped[str] = mapped_column(String(512), nullable=False)
    source_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class AssistantChunk(Base):
    __tablename__ = "assistant_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "ordinal", name="uq_assistant_chunk_ordinal"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("assistant_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    embedding_dimensions: Mapped[int] = mapped_column(Integer, nullable=False)


class AssistantProjectDocument(Base):
    __tablename__ = "assistant_project_documents"
    __table_args__ = (
        UniqueConstraint("project_id", "document_id", name="uq_assistant_project_document"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("assistant_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
