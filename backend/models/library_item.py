from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class LibraryItem(Base):
    __tablename__ = "library_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    markdown_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unread")
    collection_status: Mapped[str] = mapped_column(String(32), nullable=False, default="inbox")
    project_id: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    authors: Mapped[str | None] = mapped_column(Text, nullable=True)
    journal: Mapped[str | None] = mapped_column(String(512), nullable=True)
    conference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    metadata_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)
    metadata_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reading_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    importance: Mapped[str | None] = mapped_column(String(32), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(128), nullable=True)
    method: Mapped[str | None] = mapped_column(String(128), nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(32), nullable=True)
    personal_tags: Mapped[str | None] = mapped_column(Text, nullable=True)
