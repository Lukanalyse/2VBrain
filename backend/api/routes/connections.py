from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from core.settings import get_settings
from database.session import get_db
from repositories.library_repository import LibraryRepository
from schemas.connections import (
    ConnectionCreate,
    ConnectionGraphResponse,
    ConnectionListResponse,
    ConnectionResponse,
    ConnectionSearchResponse,
    ConnectionTypesResponse,
)
from schemas.linking import LinkableType
from services.concept_manager import ConceptManager, ConceptManagerError
from services.connection_manager import ConnectionManager, ConnectionManagerError
from services.linking_engine import LinkingEngine, LinkingEngineError
from services.vault_manager import VaultManager

router = APIRouter()


def get_connection_manager(db: Session = Depends(get_db)) -> ConnectionManager:
    settings = get_settings()
    repository = LibraryRepository(db)
    vault_manager = VaultManager(settings)
    concept_manager = ConceptManager(vault_manager=vault_manager, library_repository=repository)
    linking_engine = LinkingEngine(
        vault_manager=vault_manager,
        library_repository=repository,
        concept_manager=concept_manager,
    )
    return ConnectionManager(db=db, linking_engine=linking_engine)


@router.get("/search", response_model=ConnectionSearchResponse)
def search_objects(
    q: str = Query(default=""),
    types: list[LinkableType] | None = Query(default=None),
    manager: ConnectionManager = Depends(get_connection_manager),
) -> ConnectionSearchResponse:
    try:
        return ConnectionSearchResponse(objects=manager.search(q, types))
    except (ConceptManagerError, LinkingEngineError, ConnectionManagerError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/relation-types", response_model=ConnectionTypesResponse)
def relation_types(
    manager: ConnectionManager = Depends(get_connection_manager),
) -> ConnectionTypesResponse:
    return ConnectionTypesResponse(relation_types=manager.relation_types())


@router.get("/graph", response_model=ConnectionGraphResponse)
def graph_data(
    manager: ConnectionManager = Depends(get_connection_manager),
) -> ConnectionGraphResponse:
    try:
        return manager.graph_data()
    except (ConceptManagerError, LinkingEngineError, ConnectionManagerError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{object_id}", response_model=ConnectionListResponse)
def list_connections(
    object_id: str,
    manager: ConnectionManager = Depends(get_connection_manager),
) -> ConnectionListResponse:
    try:
        return manager.list_connections(object_id)
    except (ConceptManagerError, LinkingEngineError, ConnectionManagerError) as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/{object_id}", response_model=ConnectionResponse)
def create_connection(
    object_id: str,
    payload: ConnectionCreate,
    manager: ConnectionManager = Depends(get_connection_manager),
) -> ConnectionResponse:
    try:
        return manager.create_connection(
            source_id=object_id,
            target_id=payload.target_id,
            relation_type=payload.relation_type,
        )
    except (ConceptManagerError, LinkingEngineError, ConnectionManagerError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: str,
    manager: ConnectionManager = Depends(get_connection_manager),
) -> Response:
    try:
        manager.delete_connection(connection_id)
    except ConnectionManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
