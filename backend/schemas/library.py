from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class DuplicateStrategy(StrEnum):
    cancel = "cancel"
    replace = "replace"
    keep_both = "keep_both"


class LibraryItemResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_path: str
    markdown_path: str
    imported_at: datetime
    status: str
    collection_status: str = "inbox"
    project_id: str | None = None
    title: str | None = None
    authors: str | None = None
    journal: str | None = None
    conference: str | None = None
    year: int | None = None
    doi: str | None = None
    abstract: str | None = None
    keywords: str | None = None
    publisher: str | None = None
    source_url: str | None = None
    metadata_source: str | None = None
    metadata_confidence: str | None = None
    metadata_updated_at: datetime | None = None
    reading_progress: int = 0
    importance: str | None = None
    priority: str | None = None
    domain: str | None = None
    method: str | None = None
    difficulty: str | None = None
    personal_tags: str | None = None

    model_config = {"from_attributes": True}


class PdfMetadataPreviewResponse(BaseModel):
    title: str = ""
    authors: str = ""
    journal: str = ""
    conference: str = ""
    year: int | None = None
    doi: str = ""
    abstract: str = ""
    keywords: str = ""
    publisher: str = ""
    source_url: str = ""
    metadata_source: str = "pdf"
    metadata_confidence: str = "low"
    reading_status: str = "unread"
    reading_progress: int = 0
    importance: str = ""
    priority: str = "normal"
    domain: str = ""
    method: str = ""
    difficulty: str = ""
    personal_tags: str = ""
    project_id: str = ""


class LibraryImportConflictResponse(BaseModel):
    reason: str = "already_imported"
    message: str
    existing_item: LibraryItemResponse


class LibraryListResponse(BaseModel):
    items: list[LibraryItemResponse]
