from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.settings import get_settings
from database.session import get_db
from repositories.library_repository import LibraryRepository
from schemas.linking import LinkableType
from schemas.research_explorer import ExplorerObjectDetail, ExplorerSearchResponse
from services.concept_manager import ConceptManager, ConceptManagerError
from services.linking_engine import LinkingEngine, LinkingEngineError
from services.research_explorer import ResearchExplorer, ResearchExplorerError
from services.vault_manager import VaultManager

router = APIRouter()


def get_research_explorer(db: Session = Depends(get_db)) -> ResearchExplorer:
    settings = get_settings()
    repository = LibraryRepository(db)
    vault_manager = VaultManager(settings)
    concept_manager = ConceptManager(vault_manager=vault_manager, library_repository=repository)
    linking_engine = LinkingEngine(
        vault_manager=vault_manager,
        library_repository=repository,
        concept_manager=concept_manager,
    )
    return ResearchExplorer(linking_engine)


@router.get("/search", response_model=ExplorerSearchResponse)
def search(
    q: str = Query(default=""),
    types: list[LinkableType] | None = Query(default=None),
    explorer: ResearchExplorer = Depends(get_research_explorer),
) -> ExplorerSearchResponse:
    try:
        return ExplorerSearchResponse(objects=explorer.search(q, types))
    except (ConceptManagerError, LinkingEngineError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/objects/{object_id}", response_model=ExplorerObjectDetail)
def detail(
    object_id: str,
    explorer: ResearchExplorer = Depends(get_research_explorer),
) -> ExplorerObjectDetail:
    try:
        return explorer.get_detail(object_id)
    except (ConceptManagerError, LinkingEngineError, ResearchExplorerError) as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
