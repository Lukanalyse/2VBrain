import json
from urllib.parse import urlparse

from core.settings import Settings
from schemas.assistant import AssistantConfigResponse, AssistantConfigUpdate


class AssistantConfigError(Exception):
    pass


class AssistantConfigManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._path = settings.assistant_config_path

    def read(self) -> AssistantConfigResponse:
        data = self._read_json()
        chat_model = str(data.get("chat_model") or self._settings.ollama_chat_model)
        embedding_model = str(data.get("embedding_model") or self._settings.ollama_embedding_model)
        context_length = int(data.get("context_length") or self._settings.ollama_context_length)
        self._validate_local_model(chat_model)
        self._validate_local_model(embedding_model)
        return AssistantConfigResponse(
            base_url=self._local_base_url(),
            chat_model=chat_model,
            embedding_model=embedding_model,
            context_length=context_length,
        )

    def save(self, update: AssistantConfigUpdate) -> AssistantConfigResponse:
        self._validate_local_model(update.chat_model)
        self._validate_local_model(update.embedding_model)
        payload = {
            "chat_model": update.chat_model.strip(),
            "embedding_model": update.embedding_model.strip(),
            "context_length": update.context_length,
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return self.read()

    def _read_json(self) -> dict[str, object]:
        if not self._path.exists():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AssistantConfigError(f"Unable to read local AI configuration: {error}") from error
        return data if isinstance(data, dict) else {}

    def _local_base_url(self) -> str:
        value = self._settings.ollama_base_url.rstrip("/")
        parsed = urlparse(value)
        allowed_hosts = {"127.0.0.1", "localhost"}
        if self._settings.runtime_environment.lower() == "docker":
            allowed_hosts.add("host.docker.internal")
        if (
            parsed.scheme != "http"
            or parsed.hostname not in allowed_hosts
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise AssistantConfigError("Ollama must use the local loopback interface.")
        return value

    def _validate_local_model(self, model: str) -> None:
        value = model.strip().lower()
        if not value:
            raise AssistantConfigError("An Ollama model name is required.")
        if "cloud" in value:
            raise AssistantConfigError("Cloud-hosted Ollama models are disabled in Research OS.")
