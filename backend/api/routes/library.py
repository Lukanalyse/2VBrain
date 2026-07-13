from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from core.settings import get_settings
from database.session import get_db
from repositories.library_repository import LibraryRepository
from schemas.library import (
    DuplicateStrategy,
    LibraryImportConflictResponse,
    LibraryItemResponse,
    LibraryListResponse,
    PdfMetadataPreviewResponse,
)
from services.library_manager import (
    IncomingDocument,
    LibraryConflictError,
    LibraryImportError,
    LibraryManager,
)
from services.vault_manager import VaultManager

router = APIRouter()


def get_library_manager(db: Session = Depends(get_db)) -> LibraryManager:
    settings = get_settings()
    return LibraryManager(
        settings=settings,
        repository=LibraryRepository(db),
        vault_manager=VaultManager(settings),
    )


@router.get("", response_model=LibraryListResponse)
def list_library_items(
    manager: LibraryManager = Depends(get_library_manager),
) -> LibraryListResponse:
    return LibraryListResponse(items=manager.list_items())


@router.post("/preview", response_model=PdfMetadataPreviewResponse)
def preview_pdf(
    file: UploadFile = File(...),
    manager: LibraryManager = Depends(get_library_manager),
) -> PdfMetadataPreviewResponse:
    try:
        return manager.preview_pdf_metadata(
            IncomingDocument(
                filename=file.filename or "Untitled Paper.pdf",
                file=file.file,
                content_type=file.content_type,
            )
        )
    except LibraryImportError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/import", response_model=LibraryItemResponse)
def import_pdf(
    file: UploadFile = File(...),
    duplicate_strategy: DuplicateStrategy = Query(default=DuplicateStrategy.cancel),
    title: str = Form(default=""),
    authors: str = Form(default=""),
    journal: str = Form(default=""),
    conference: str = Form(default=""),
    year: int | None = Form(default=None),
    doi: str = Form(default=""),
    abstract: str = Form(default=""),
    keywords: str = Form(default=""),
    publisher: str = Form(default=""),
    source_url: str = Form(default=""),
    metadata_source: str = Form(default="pdf"),
    metadata_confidence: str = Form(default="low"),
    reading_status: str = Form(default="unread"),
    reading_progress: int = Form(default=0),
    importance: str = Form(default=""),
    priority: str = Form(default="normal"),
    domain: str = Form(default=""),
    method: str = Form(default=""),
    difficulty: str = Form(default=""),
    personal_tags: str = Form(default=""),
    project_id: str = Form(default=""),
    manager: LibraryManager = Depends(get_library_manager),
) -> LibraryItemResponse:
    try:
        item = manager.import_pdf(
            IncomingDocument(
                filename=file.filename or "Untitled Paper.pdf",
                file=file.file,
                content_type=file.content_type,
            ),
            duplicate_strategy=duplicate_strategy,
            metadata=PdfMetadataPreviewResponse(
                title=title,
                authors=authors,
                journal=journal,
                conference=conference,
                year=year,
                doi=doi,
                abstract=abstract,
                keywords=keywords,
                publisher=publisher,
                source_url=source_url,
                metadata_source=metadata_source,
                metadata_confidence=metadata_confidence,
                reading_status=reading_status,
                reading_progress=reading_progress,
                importance=importance,
                priority=priority,
                domain=domain,
                method=method,
                difficulty=difficulty,
                personal_tags=personal_tags,
                project_id=project_id,
            ),
        )
    except LibraryConflictError as error:
        conflict = LibraryImportConflictResponse(
            message=str(error),
            existing_item=LibraryItemResponse.model_validate(error.existing_item),
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict.model_dump(mode="json"),
        ) from error
    except LibraryImportError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return LibraryItemResponse.model_validate(item)
