import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from schemas.assistant import AssistantModelInfo, GroundedAnswerPayload


class OllamaError(Exception):
    pass


class OllamaClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def list_models(self) -> list[AssistantModelInfo]:
        payload = self._request("/api/tags", timeout=3)
        models = payload.get("models", [])
        if not isinstance(models, list):
            return []
        result: list[AssistantModelInfo] = []
        for model in models:
            if not isinstance(model, dict):
                continue
            name = str(model.get("name") or model.get("model") or "").strip()
            if not name or "cloud" in name.lower():
                continue
            details = model.get("details") if isinstance(model.get("details"), dict) else {}
            result.append(
                AssistantModelInfo(
                    name=name,
                    size=model.get("size") if isinstance(model.get("size"), int) else None,
                    parameter_size=str(details.get("parameter_size") or "") or None,
                    quantization_level=str(details.get("quantization_level") or "") or None,
                )
            )
        return sorted(result, key=lambda item: item.name.lower())

    def embed(self, texts: list[str], model: str) -> list[list[float]]:
        if not texts:
            return []
        payload = self._request(
            "/api/embed",
            {"model": model, "input": texts, "truncate": False},
            timeout=300,
        )
        embeddings = payload.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise OllamaError("Ollama returned an invalid embedding response.")
        try:
            return [[float(value) for value in embedding] for embedding in embeddings]
        except (TypeError, ValueError) as error:
            raise OllamaError("Ollama returned malformed embeddings.") from error

    def grounded_answer(
        self,
        *,
        model: str,
        context_length: int,
        messages: list[dict[str, str]],
        allowed_citations: list[str],
    ) -> GroundedAnswerPayload:
        schema = GroundedAnswerPayload.model_json_schema()
        primary_schema = schema["properties"]["primary_citation"]
        primary_schema["enum"] = [*allowed_citations, "NONE"]
        citation_schema = schema["properties"]["citations"]
        citation_schema["items"] = {
            "type": "string",
            "enum": allowed_citations,
        }
        payload = self._request(
            "/api/chat",
            {
                "model": model,
                "messages": messages,
                "stream": False,
                "think": False,
                "format": schema,
                "keep_alive": "10m",
                "options": {"temperature": 0.1, "num_ctx": context_length},
            },
            timeout=600,
        )
        message = payload.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise OllamaError("Ollama returned an invalid chat response.")
        try:
            return GroundedAnswerPayload.model_validate_json(content)
        except ValueError as error:
            raise OllamaError(
                "Ollama did not return the required grounded answer format."
            ) from error

    def _request(
        self,
        path: str,
        payload: dict[str, object] | None = None,
        *,
        timeout: int,
    ) -> dict[str, object]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self._base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"} if data is not None else {},
            method="POST" if data is not None else "GET",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            raise OllamaError(f"Unable to reach local Ollama: {error}") from error
        if not isinstance(result, dict):
            raise OllamaError("Ollama returned an unexpected response.")
        return result
