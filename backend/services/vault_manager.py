import json
import logging
import os
from pathlib import Path
from typing import Any

from core.settings import Settings
from schemas.storage import StorageStatusResponse, VaultValidationResponse

logger = logging.getLogger(__name__)


class VaultManager:
    """Owns vault path configuration and validation only."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._config_path = settings.workspace_config_path

    def get_storage_status(self) -> StorageStatusResponse:
        configured_vault = self._read_config().get("vault_path")
        vault_path = Path(configured_vault) if configured_vault else None
        vault_path = self._runtime_vault_root(vault_path)
        validation = self.validate_vault(vault_path) if vault_path else None

        return StorageStatusResponse(
            is_configured=validation.is_valid if validation else False,
            vault_path=vault_path,
            library_path=self._settings.library_path,
            database_url=self._settings.database_url,
            vector_store_path=None,
            vector_store_provider=self._settings.vector_store_provider,
            validation_message=validation.message if validation else "No vault configured.",
        )

    def validate_vault(self, vault_path: Path | None) -> VaultValidationResponse:
        received_path = str(vault_path) if vault_path is not None else None
        logger.info(
            "Validating Obsidian vault path",
            extra={
                "component": "backend.vault_manager",
                "received_path": received_path,
                "runtime_environment": self._settings.runtime_environment,
            },
        )

        if vault_path is None:
            logger.warning(
                "Vault validation failed: missing path",
                extra={
                    "component": "backend.vault_manager",
                    "failed_check": "path_required",
                    "received_path": received_path,
                },
            )
            return VaultValidationResponse(
                is_valid=False,
                vault_path=Path(),
                message="Vault path is required.",
                error_code="path_required",
                received_path=received_path,
                normalized_path=Path(),
                failed_check="path_required",
            )

        try:
            expanded_path = vault_path.expanduser().resolve(strict=False)
        except OSError as error:
            logger.warning(
                "Vault validation failed while normalizing path",
                extra={
                    "component": "backend.vault_manager",
                    "failed_check": "normalize_path",
                    "received_path": received_path,
                    "system_error": str(error),
                },
            )
            return VaultValidationResponse(
                is_valid=False,
                vault_path=vault_path,
                message=f"Unable to normalize vault path: {error}.",
                error_code="path_normalization_failed",
                received_path=received_path,
                normalized_path=vault_path,
                failed_check="normalize_path",
                system_error=str(error),
            )

        try:
            exists = expanded_path.exists()
        except OSError as error:
            logger.warning(
                "Vault validation failed while checking existence",
                extra={
                    "component": "backend.vault_manager",
                    "failed_check": "exists",
                    "received_path": received_path,
                    "normalized_path": str(expanded_path),
                    "system_error": str(error),
                },
            )
            return VaultValidationResponse(
                is_valid=False,
                vault_path=expanded_path,
                message=f"Unable to access folder: {error}.",
                error_code="folder_inaccessible",
                received_path=received_path,
                normalized_path=expanded_path,
                failed_check="exists",
                system_error=str(error),
            )

        if not exists:
            is_docker_path_issue = self._is_likely_unmounted_host_path(expanded_path)
            message = (
                "Folder does not exist inside the Docker container. If this path exists on "
                "the host, mount it into the backend container."
                if is_docker_path_issue
                else "Folder does not exist."
            )
            logger.warning(
                "Vault validation failed: folder does not exist",
                extra={
                    "component": "backend.vault_manager",
                    "failed_check": "exists",
                    "received_path": received_path,
                    "normalized_path": str(expanded_path),
                    "is_docker_path_issue": is_docker_path_issue,
                },
            )
            return VaultValidationResponse(
                is_valid=False,
                vault_path=expanded_path,
                message=message,
                error_code="folder_not_found",
                received_path=received_path,
                normalized_path=expanded_path,
                failed_check="exists",
                is_docker_path_issue=is_docker_path_issue,
            )

        try:
            is_dir = expanded_path.is_dir()
        except OSError as error:
            logger.warning(
                "Vault validation failed while checking directory",
                extra={
                    "component": "backend.vault_manager",
                    "failed_check": "is_dir",
                    "received_path": received_path,
                    "normalized_path": str(expanded_path),
                    "system_error": str(error),
                },
            )
            return VaultValidationResponse(
                is_valid=False,
                vault_path=expanded_path,
                message=f"Unable to inspect folder: {error}.",
                error_code="folder_inaccessible",
                received_path=received_path,
                normalized_path=expanded_path,
                failed_check="is_dir",
                system_error=str(error),
            )

        if not is_dir:
            logger.warning(
                "Vault validation failed: path is not a folder",
                extra={
                    "component": "backend.vault_manager",
                    "failed_check": "is_dir",
                    "received_path": received_path,
                    "normalized_path": str(expanded_path),
                },
            )
            return VaultValidationResponse(
                is_valid=False,
                vault_path=expanded_path,
                message="Path is not a folder.",
                error_code="not_a_directory",
                received_path=received_path,
                normalized_path=expanded_path,
                failed_check="is_dir",
            )

        obsidian_dir = expanded_path / ".obsidian"
        try:
            has_obsidian_dir = obsidian_dir.is_dir()
        except OSError as error:
            logger.warning(
                "Vault validation failed while checking .obsidian",
                extra={
                    "component": "backend.vault_manager",
                    "failed_check": "obsidian_dir",
                    "received_path": received_path,
                    "normalized_path": str(expanded_path),
                    "system_error": str(error),
                },
            )
            return VaultValidationResponse(
                is_valid=False,
                vault_path=expanded_path,
                message=f"Unable to inspect .obsidian directory: {error}.",
                error_code="permission_denied",
                received_path=received_path,
                normalized_path=expanded_path,
                failed_check="obsidian_dir",
                system_error=str(error),
            )

        if not has_obsidian_dir:
            logger.warning(
                "Vault validation failed: missing .obsidian directory",
                extra={
                    "component": "backend.vault_manager",
                    "failed_check": "obsidian_dir",
                    "received_path": received_path,
                    "normalized_path": str(expanded_path),
                },
            )
            return VaultValidationResponse(
                is_valid=False,
                vault_path=expanded_path,
                message="Folder is not an Obsidian vault. Missing .obsidian directory.",
                error_code="missing_obsidian_directory",
                received_path=received_path,
                normalized_path=expanded_path,
                failed_check="obsidian_dir",
            )

        logger.info(
            "Vault validation succeeded",
            extra={
                "component": "backend.vault_manager",
                "received_path": received_path,
                "normalized_path": str(expanded_path),
            },
        )
        return VaultValidationResponse(
            is_valid=True,
            vault_path=expanded_path,
            message="Valid Obsidian vault.",
            error_code=None,
            received_path=received_path,
            normalized_path=expanded_path,
        )

    def save_vault_path(self, vault_path: Path) -> StorageStatusResponse:
        validation = self.validate_vault(vault_path)
        if not validation.is_valid:
            return self.get_storage_status().model_copy(
                update={
                    "is_configured": False,
                    "vault_path": validation.vault_path,
                    "validation_message": validation.message,
                }
            )

        self._write_config({"vault_path": str(validation.vault_path)})
        return self.get_storage_status()

    def _read_config(self) -> dict[str, Any]:
        if not self._config_path.exists():
            return {}

        with self._config_path.open("r", encoding="utf-8") as config_file:
            data = json.load(config_file)

        return data if isinstance(data, dict) else {}

    def _write_config(self, data: dict[str, Any]) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with self._config_path.open("w", encoding="utf-8") as config_file:
            json.dump(data, config_file, indent=2)
            config_file.write("\n")

    def _runtime_vault_root(self, vault_path: Path | None) -> Path | None:
        """Map the configured vault root to one valid in the current runtime.

        workspace.json is shared between local dev and Docker (config/ is
        bind-mounted). In Docker the vault is mounted at settings.vault_path
        (/app/vault), so a stored host root like /Users/... is not reachable.
        When the configured root does not exist here, fall back to the mount.
        In local dev the configured root exists and is returned unchanged.
        """
        if vault_path is None:
            return None
        try:
            if vault_path.exists():
                return vault_path
        except OSError:
            pass
        if self._settings.runtime_environment.lower() == "docker":
            return self._settings.vault_path
        return vault_path

    def resolve_vault_file(self, stored_path: str | Path) -> Path:
        """Rebase a stored vault file path onto the current runtime vault root.

        The database stores absolute paths anchored to whatever vault root was
        configured when the row was written (e.g. a host path like /Users/...).
        Rebasing the vault-relative portion onto the runtime root keeps stored
        paths working across host/container and vault moves, without rewriting
        the database. Paths outside the vault (e.g. library PDFs) and local-dev
        paths are returned resolved but otherwise unchanged.
        """
        path = Path(stored_path).expanduser()
        configured = self._read_config().get("vault_path")
        if configured:
            configured_root = Path(configured).expanduser()
            runtime_root = self._runtime_vault_root(configured_root)
            if runtime_root is not None and runtime_root != configured_root:
                try:
                    relative = path.relative_to(configured_root)
                except ValueError:
                    relative = None
                if relative is not None:
                    return (runtime_root / relative).resolve()
        return path.resolve()

    def is_managed_content_path(self, path: str | Path) -> bool:
        """Return whether a resolved file stays inside the configured data roots."""
        try:
            resolved = Path(path).expanduser().resolve(strict=False)
        except OSError:
            return False

        roots: list[Path] = []
        configured = self._read_config().get("vault_path")
        if configured:
            configured_root = Path(configured).expanduser()
            runtime_root = self._runtime_vault_root(configured_root)
            if runtime_root is not None:
                roots.append(runtime_root)
        roots.append(self._settings.library_path)

        for root in roots:
            try:
                resolved.relative_to(root.expanduser().resolve(strict=False))
            except (OSError, ValueError):
                continue
            return True
        return False

    def _is_likely_unmounted_host_path(self, path: Path) -> bool:
        if self._settings.runtime_environment.lower() != "docker":
            return False

        path_text = str(path)
        home = os.environ.get("HOME")
        return (
            path.is_absolute()
            and home is not None
            and not path_text.startswith(home)
            and (path_text.startswith("/Users/") or path_text.startswith("/home/"))
        )
