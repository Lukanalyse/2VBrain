from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.settings import get_settings
from database.session import get_db
from repositories.library_repository import LibraryRepository
from schemas.concept import ConceptCreate, ConceptDetailResponse, ConceptListResponse, ConceptResponse
from schemas.library import LibraryItemResponse
from services.concept_manager import ConceptManager, ConceptManagerError
from services.vault_manager import VaultManager

router = APIRouter()


def get_concept_manager(db: Session = Depends(get_db)) -> ConceptManager:
    settings = get_settings()
    return ConceptManager(
        vault_manager=VaultManager(settings),
        library_repository=LibraryRepository(db),
    )


@router.get("", response_model=ConceptListResponse)
def list_concepts(manager: ConceptManager = Depends(get_concept_manager)) -> ConceptListResponse:
    try:
        return ConceptListResponse(concepts=manager.list_concepts())
    except ConceptManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("", response_model=ConceptResponse)
def create_concept(
    payload: ConceptCreate,
    manager: ConceptManager = Depends(get_concept_manager),
) -> ConceptResponse:
    try:
        return manager.create_concept(payload)
    except ConceptManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{slug}", response_model=ConceptDetailResponse)
def read_concept(
    slug: str,
    manager: ConceptManager = Depends(get_concept_manager),
) -> ConceptDetailResponse:
    try:
        concept, content, linked_papers = manager.get_concept_detail(slug)
    except ConceptManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    return ConceptDetailResponse(
        concept=concept,
        content=content,
        linked_papers=[LibraryItemResponse.model_validate(item) for item in linked_papers],
    )
