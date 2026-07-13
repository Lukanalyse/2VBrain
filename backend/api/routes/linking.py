from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.settings import get_settings
from database.session import get_db
from repositories.library_repository import LibraryRepository
from schemas.linking import (
    LinkCreateRequest,
    LinkCreateResponse,
    LinkSearchResponse,
    LinkableType,
    ObjectRelations,
)
from services.concept_manager import ConceptManager, ConceptManagerError
from services.linking_engine import LinkingEngine, LinkingEngineError
from services.vault_manager import VaultManager

router = APIRouter()


def get_linking_engine(db: Session = Depends(get_db)) -> LinkingEngine:
    settings = get_settings()
    repository = LibraryRepository(db)
    vault_manager = VaultManager(settings)
    concept_manager = ConceptManager(vault_manager=vault_manager, library_repository=repository)
    return LinkingEngine(
        vault_manager=vault_manager,
        library_repository=repository,
        concept_manager=concept_manager,
    )


@router.get("/search", response_model=LinkSearchResponse)
def search_linkable_objects(
    q: str = Query(default=""),
    types: list[LinkableType] | None = Query(default=None),
    engine: LinkingEngine = Depends(get_linking_engine),
) -> LinkSearchResponse:
    try:
        return LinkSearchResponse(objects=engine.search(q, types))
    except (ConceptManagerError, LinkingEngineError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{source_id}/relations", response_model=ObjectRelations)
def read_relations(
    source_id: str,
    engine: LinkingEngine = Depends(get_linking_engine),
) -> ObjectRelations:
    try:
        return engine.get_relations(source_id)
    except (ConceptManagerError, LinkingEngineError) as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/{source_id}", response_model=LinkCreateResponse)
def create_links(
    source_id: str,
    payload: LinkCreateRequest,
    engine: LinkingEngine = Depends(get_linking_engine),
) -> LinkCreateResponse:
    try:
        source = engine.get_relations(source_id).source
        targets = engine.link(source_id, payload.target_ids)
    except (ConceptManagerError, LinkingEngineError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return LinkCreateResponse(source=source, targets=targets)
