from pathlib import Path

from core.settings import Settings
from services.vault_manager import VaultManager


def make_manager(tmp_path: Path) -> VaultManager:
    return VaultManager(
        Settings(
            workspace_config_path=tmp_path / "workspace.json",
            library_path=tmp_path / "library",
        )
    )


def test_validate_rejects_non_vault_folder(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    folder = tmp_path / "notes"
    folder.mkdir()

    result = manager.validate_vault(folder)

    assert result.is_valid is False
    assert "Missing .obsidian" in result.message
    assert result.error_code == "missing_obsidian_directory"
    assert result.failed_check == "obsidian_dir"


def test_save_valid_vault_path(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)

    result = manager.save_vault_path(vault)

    assert result.is_configured is True
    assert result.vault_path == vault.resolve()


def test_validate_rejects_missing_folder_with_diagnostics(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)

    result = manager.validate_vault(tmp_path / "missing")

    assert result.is_valid is False
    assert result.error_code == "folder_not_found"
    assert result.failed_check == "exists"
    assert result.received_path is not None
    assert result.normalized_path is not None


def test_validate_rejects_file_path(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    file_path = tmp_path / "not-a-folder.md"
    file_path.write_text("content", encoding="utf-8")

    result = manager.validate_vault(file_path)

    assert result.is_valid is False
    assert result.error_code == "not_a_directory"
    assert result.failed_check == "is_dir"
