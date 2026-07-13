from pathlib import Path

from pydantic import BaseModel


class VaultValidationRequest(BaseModel):
    vault_path: Path


class VaultValidationResponse(BaseModel):
    is_valid: bool
    vault_path: Path
    message: str
    error_code: str | None = None
    received_path: str | None = None
    normalized_path: Path | None = None
    validated_by: str = "backend"
    failed_check: str | None = None
    system_error: str | None = None
    is_docker_path_issue: bool = False


class WorkspaceStorageUpdate(BaseModel):
    vault_path: Path


class StorageStatusResponse(BaseModel):
    is_configured: bool
    vault_path: Path | None
    library_path: Path
    database_url: str
    vector_store_path: Path | None
    vector_store_provider: str | None
    validation_message: str | None = None
