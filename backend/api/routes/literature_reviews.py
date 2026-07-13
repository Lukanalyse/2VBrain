from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.settings import get_settings
from database.session import get_db
from repositories.library_repository import LibraryRepository
from schemas.literature_review import (
    LiteratureReviewCreate,
    LiteratureReviewDetail,
    LiteratureReviewList,
)
from services.concept_manager import ConceptManager
from services.linking_engine import LinkingEngine
from services.literature_review_manager import (
    LiteratureReviewManager,
    LiteratureReviewManagerError,
)
from services.vault_manager import VaultManager

router = APIRouter()


class LiteratureReviewSave(BaseModel):
    content: str


def get_literature_review_manager(db: Session = Depends(get_db)) -> LiteratureReviewManager:
    settings = get_settings()
    repository = LibraryRepository(db)
    vault_manager = VaultManager(settings)
    concept_manager = ConceptManager(vault_manager=vault_manager, library_repository=repository)
    linking_engine = LinkingEngine(
        vault_manager=vault_manager,
        library_repository=repository,
        concept_manager=concept_manager,
    )
    return LiteratureReviewManager(vault_manager=vault_manager, linking_engine=linking_engine)


@router.get("", response_model=LiteratureReviewList)
def list_reviews(
    manager: LiteratureReviewManager = Depends(get_literature_review_manager),
) -> LiteratureReviewList:
    return LiteratureReviewList(reviews=manager.list_reviews())


@router.post("", response_model=LiteratureReviewDetail)
def create_review(
    payload: LiteratureReviewCreate,
    manager: LiteratureReviewManager = Depends(get_literature_review_manager),
) -> LiteratureReviewDetail:
    try:
        review = manager.create_review(payload.title)
        _, content = manager.get_review(review.title)
        return LiteratureReviewDetail(review=review, content=content)
    except LiteratureReviewManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{slug}", response_model=LiteratureReviewDetail)
def read_review(
    slug: str,
    manager: LiteratureReviewManager = Depends(get_literature_review_manager),
) -> LiteratureReviewDetail:
    try:
        review, content = manager.get_review(slug)
        return LiteratureReviewDetail(review=review, content=content)
    except LiteratureReviewManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.put("/{slug}", response_model=LiteratureReviewDetail)
def save_review(
    slug: str,
    payload: LiteratureReviewSave,
    manager: LiteratureReviewManager = Depends(get_literature_review_manager),
) -> LiteratureReviewDetail:
    try:
        review, content = manager.save_review(slug, payload.content)
        return LiteratureReviewDetail(review=review, content=content)
    except LiteratureReviewManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
