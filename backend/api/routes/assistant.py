from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.settings import get_settings
from database.session import get_db
from repositories.assistant_repository import AssistantRepository
from repositories.library_repository import LibraryRepository
from schemas.assistant import (
    AssistantConfigResponse,
    AssistantConfigUpdate,
    AssistantStatusResponse,
    ProjectAssistantQuery,
    ProjectAssistantResponse,
    ProjectIndexStatus,
)
from services.assistant_config_manager import AssistantConfigError, AssistantConfigManager
from services.concept_manager import ConceptManager
from services.hybrid_retriever import HybridRetriever
from services.linking_engine import LinkingEngine
from services.ollama_client import OllamaClient, OllamaError
from services.project_assistant import ProjectAssistant, ProjectAssistantError
from services.project_corpus import ProjectCorpusError, ProjectCorpusResolver
from services.project_indexer import ProjectIndexer
from services.vault_manager import VaultManager

router = APIRouter()


def build_assistant(db: Session | None = None) -> ProjectAssistant:
    settings = get_settings()
    config_manager = AssistantConfigManager(settings)
    config = config_manager.read()
    ollama = OllamaClient(config.base_url)

    if db is None:
        return ProjectAssistant(
            config_manager=config_manager,
            ollama=ollama,
        )

    library_repository = LibraryRepository(db)
    vault_manager = VaultManager(settings)
    concept_manager = ConceptManager(
        vault_manager=vault_manager,
        library_repository=library_repository,
    )
    linking_engine = LinkingEngine(
        vault_manager=vault_manager,
        library_repository=library_repository,
        concept_manager=concept_manager,
    )
    assistant_repository = AssistantRepository(db)
    resolver = ProjectCorpusResolver(
        vault_manager=vault_manager,
        library_repository=library_repository,
        linking_engine=linking_engine,
    )
    indexer = ProjectIndexer(
        corpus_resolver=resolver,
        repository=assistant_repository,
        ollama=ollama,
    )
    return ProjectAssistant(
        config_manager=config_manager,
        ollama=ollama,
        indexer=indexer,
        retriever=HybridRetriever(assistant_repository),
    )


def get_project_assistant(
    db: Annotated[Session, Depends(get_db)],
) -> ProjectAssistant:
    return build_assistant(db)


ProjectAssistantDependency = Annotated[ProjectAssistant, Depends(get_project_assistant)]


@router.get("/config", response_model=AssistantConfigResponse)
def read_assistant_config() -> AssistantConfigResponse:
    try:
        return build_assistant().config()
    except AssistantConfigError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)
        ) from error


@router.put("/config", response_model=AssistantConfigResponse)
def update_assistant_config(payload: AssistantConfigUpdate) -> AssistantConfigResponse:
    try:
        return build_assistant().save_config(payload)
    except AssistantConfigError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/status", response_model=AssistantStatusResponse)
def read_assistant_status() -> AssistantStatusResponse:
    try:
        return build_assistant().status()
    except AssistantConfigError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)
        ) from error


@router.get("/projects/{project_id}/index", response_model=ProjectIndexStatus)
def read_project_index(
    project_id: str, assistant: ProjectAssistantDependency
) -> ProjectIndexStatus:
    try:
        return assistant.index_status(project_id)
    except (AssistantConfigError, ProjectAssistantError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/projects/{project_id}/index", response_model=ProjectIndexStatus)
def index_project(project_id: str, assistant: ProjectAssistantDependency) -> ProjectIndexStatus:
    try:
        return assistant.index_project(project_id)
    except ProjectCorpusError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except OllamaError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
        ) from error
    except (AssistantConfigError, ProjectAssistantError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/projects/{project_id}/query", response_model=ProjectAssistantResponse)
def query_project(
    project_id: str,
    payload: ProjectAssistantQuery,
    assistant: ProjectAssistantDependency,
) -> ProjectAssistantResponse:
    try:
        return assistant.answer(project_id, payload)
    except ProjectCorpusError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except OllamaError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
        ) from error
    except (AssistantConfigError, ProjectAssistantError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
