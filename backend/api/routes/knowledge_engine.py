from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.settings import get_settings
from database.session import get_db
from repositories.library_repository import LibraryRepository
from schemas.knowledge_engine import (
    ConceptConceptLinksResponse,
    ConceptConceptLinksUpdate,
    KnowledgeConceptView,
    KnowledgeExploreListResponse,
)
from services.concept_manager import ConceptManager, ConceptManagerError
from services.knowledge_engine import KnowledgeEngine
from services.vault_manager import VaultManager

router = APIRouter()


def get_knowledge_engine(db: Session = Depends(get_db)) -> KnowledgeEngine:
    settings = get_settings()
    concept_manager = ConceptManager(
        vault_manager=VaultManager(settings),
        library_repository=LibraryRepository(db),
    )
    return KnowledgeEngine(concept_manager)


@router.get("/concepts", response_model=KnowledgeExploreListResponse)
def list_explore_concepts(
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> KnowledgeExploreListResponse:
    try:
        return KnowledgeExploreListResponse(concepts=engine.list_concepts())
    except ConceptManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/concepts/{slug}", response_model=KnowledgeConceptView)
def read_explore_concept(
    slug: str,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> KnowledgeConceptView:
    try:
        return engine.get_concept_view(slug)
    except ConceptManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.put("/concepts/{slug}/concepts", response_model=ConceptConceptLinksResponse)
def update_related_concepts(
    slug: str,
    payload: ConceptConceptLinksUpdate,
    engine: KnowledgeEngine = Depends(get_knowledge_engine),
) -> ConceptConceptLinksResponse:
    try:
        concept_names = engine.link_related_concepts(slug, payload.concept_names)
    except ConceptManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return ConceptConceptLinksResponse(concept_names=concept_names)
