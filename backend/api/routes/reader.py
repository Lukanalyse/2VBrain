import platform
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from core.settings import get_settings
from models.library_item import LibraryItem
from repositories.library_repository import LibraryRepository
from schemas.concept import PaperConceptLinksResponse, PaperConceptLinksUpdate
from schemas.library import LibraryItemResponse
from schemas.reader import MarkdownDocumentResponse, MarkdownDocumentUpdate
from services.concept_manager import ConceptManager, ConceptManagerError
from services.reader_manager import ReaderManager, ReaderManagerError
from services.vault_manager import VaultManager

router = APIRouter()


def get_library_item_or_404(item_id: int, db: Session) -> LibraryItem:
    repository = LibraryRepository(db)
    item = repository.get_by_id(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library item not found.")
    return item


@router.get("/items/{item_id}", response_model=LibraryItemResponse)
def read_library_item(item_id: int, db: Session = Depends(get_db)) -> LibraryItemResponse:
    item = get_library_item_or_404(item_id, db)
    return LibraryItemResponse.model_validate(item)


@router.get("/items/{item_id}/markdown", response_model=MarkdownDocumentResponse)
def read_markdown(item_id: int, db: Session = Depends(get_db)) -> MarkdownDocumentResponse:
    item = get_library_item_or_404(item_id, db)
    manager = ReaderManager()

    try:
        content = manager.read_markdown(item)
    except ReaderManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    return MarkdownDocumentResponse(
        library_item_id=item.id,
        markdown_path=item.markdown_path,
        content=content,
    )


@router.put("/items/{item_id}/markdown", response_model=MarkdownDocumentResponse)
def save_markdown(
    item_id: int,
    payload: MarkdownDocumentUpdate,
    db: Session = Depends(get_db),
) -> MarkdownDocumentResponse:
    item = get_library_item_or_404(item_id, db)
    manager = ReaderManager()

    try:
        content = manager.save_markdown(item, payload.content)
    except ReaderManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return MarkdownDocumentResponse(
        library_item_id=item.id,
        markdown_path=item.markdown_path,
        content=content,
    )


@router.post("/items/{item_id}/open-pdf")
def open_pdf(item_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    item = get_library_item_or_404(item_id, db)
    pdf_path = Path(item.file_path).expanduser().resolve()

    if not pdf_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF file not found.")

    system = platform.system()
    if system == "Darwin":
        subprocess.Popen(["open", str(pdf_path)])
    elif system == "Windows":
        subprocess.Popen(["cmd", "/c", "start", "", str(pdf_path)])
    else:
        subprocess.Popen(["xdg-open", str(pdf_path)])

    return {"status": "opened"}


@router.get("/items/{item_id}/concepts", response_model=PaperConceptLinksResponse)
def read_paper_concepts(item_id: int, db: Session = Depends(get_db)) -> PaperConceptLinksResponse:
    item = get_library_item_or_404(item_id, db)
    settings = get_settings()
    manager = ConceptManager(
        vault_manager=VaultManager(settings),
        library_repository=LibraryRepository(db),
    )

    try:
        concept_names = manager.get_paper_concepts(item)
    except ConceptManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return PaperConceptLinksResponse(concept_names=concept_names)


@router.put("/items/{item_id}/concepts", response_model=PaperConceptLinksResponse)
def update_paper_concepts(
    item_id: int,
    payload: PaperConceptLinksUpdate,
    db: Session = Depends(get_db),
) -> PaperConceptLinksResponse:
    item = get_library_item_or_404(item_id, db)
    settings = get_settings()
    manager = ConceptManager(
        vault_manager=VaultManager(settings),
        library_repository=LibraryRepository(db),
    )

    try:
        concept_names = manager.link_paper_concepts(item, payload.concept_names)
    except ConceptManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return PaperConceptLinksResponse(concept_names=concept_names)
