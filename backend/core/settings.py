from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Research OS"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./research_os.db"
    config_path: Path = Field(default=Path("../config/research-os.yaml"))
    workspace_config_path: Path = Field(default=Path("../config/workspace.json"))

    vault_path: Path = Path("../vault")
    library_path: Path = Path("../library")
    host_vault_path: Path | None = None

    llm_provider: str | None = None
    vector_store_provider: str | None = None
    runtime_environment: str = "local"

    model_config = SettingsConfigDict(env_prefix="RESEARCH_OS_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
