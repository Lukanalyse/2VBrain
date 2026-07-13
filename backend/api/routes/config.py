from fastapi import APIRouter

from core.settings import get_settings
from schemas.config import RuntimeConfigResponse

router = APIRouter()


@router.get("", response_model=RuntimeConfigResponse)
def read_runtime_config() -> RuntimeConfigResponse:
    settings = get_settings()
    return RuntimeConfigResponse(
        vault_path=settings.vault_path,
        library_path=settings.library_path,
        llm_provider=settings.llm_provider,
        vector_store_provider=settings.vector_store_provider,
    )
