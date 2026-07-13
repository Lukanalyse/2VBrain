from fastapi import APIRouter

from core.settings import get_settings
from schemas.storage import (
    StorageStatusResponse,
    VaultValidationRequest,
    VaultValidationResponse,
    WorkspaceStorageUpdate,
)
from services.vault_manager import VaultManager

router = APIRouter()


def get_vault_manager() -> VaultManager:
    return VaultManager(get_settings())


@router.get("", response_model=StorageStatusResponse)
def read_storage_status() -> StorageStatusResponse:
    return get_vault_manager().get_storage_status()


@router.post("/vault/validate", response_model=VaultValidationResponse)
def validate_vault(payload: VaultValidationRequest) -> VaultValidationResponse:
    return get_vault_manager().validate_vault(payload.vault_path)


@router.put("/vault", response_model=StorageStatusResponse)
def update_vault(payload: WorkspaceStorageUpdate) -> StorageStatusResponse:
    return get_vault_manager().save_vault_path(payload.vault_path)

