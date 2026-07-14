from fastapi import APIRouter

from api.routes import (
    assistant,
    concepts,
    config,
    connections,
    health,
    knowledge_engine,
    library,
    linking,
    literature_reviews,
    reader,
    research_explorer,
    storage,
    workspace,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(storage.router, prefix="/storage", tags=["storage"])
api_router.include_router(library.router, prefix="/library", tags=["library"])
api_router.include_router(reader.router, prefix="/reader", tags=["reader"])
api_router.include_router(concepts.router, prefix="/concepts", tags=["concepts"])
api_router.include_router(connections.router, prefix="/connections", tags=["connections"])
api_router.include_router(knowledge_engine.router, prefix="/explore", tags=["explore"])
api_router.include_router(linking.router, prefix="/links", tags=["links"])
api_router.include_router(workspace.router, prefix="/workspace", tags=["workspace"])
api_router.include_router(
    literature_reviews.router,
    prefix="/literature-reviews",
    tags=["literature-reviews"],
)
api_router.include_router(
    research_explorer.router,
    prefix="/research-explorer",
    tags=["research-explorer"],
)
