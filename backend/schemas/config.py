from pathlib import Path

from pydantic import BaseModel


class RuntimeConfigResponse(BaseModel):
    vault_path: Path
    library_path: Path
    llm_provider: str | None
    vector_store_provider: str | None

