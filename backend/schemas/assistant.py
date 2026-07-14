from typing import Literal

from pydantic import BaseModel, Field

from schemas.linking import LinkableObject


class AssistantConfigResponse(BaseModel):
    provider: Literal["ollama"] = "ollama"
    base_url: str
    chat_model: str
    embedding_model: str
    context_length: int
    local_only: bool = True


class AssistantConfigUpdate(BaseModel):
    chat_model: str = Field(min_length=1, max_length=255)
    embedding_model: str = Field(min_length=1, max_length=255)
    context_length: int = Field(ge=4096, le=131072)


class AssistantModelInfo(BaseModel):
    name: str
    size: int | None = None
    parameter_size: str | None = None
    quantization_level: str | None = None


class AssistantStatusResponse(BaseModel):
    available: bool
    config: AssistantConfigResponse
    models: list[AssistantModelInfo] = Field(default_factory=list)
    error: str | None = None


class ProjectIndexStatus(BaseModel):
    project_id: str
    ready: bool
    document_count: int
    chunk_count: int
    embedding_model: str
    updated_documents: int = 0
    errors: list[str] = Field(default_factory=list)


class AssistantHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class ProjectAssistantQuery(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    history: list[AssistantHistoryMessage] = Field(default_factory=list, max_length=8)


class AssistantCitation(BaseModel):
    label: str
    object: LinkableObject
    source_kind: Literal["markdown", "pdf"]
    source_title: str
    heading: str
    page_number: int | None = None
    excerpt: str


class ProjectAssistantResponse(BaseModel):
    answer: str
    citations: list[AssistantCitation]
    insufficient_evidence: bool


class GroundedAnswerPayload(BaseModel):
    answer: str = Field(description="Grounded answer with exact inline source labels such as [S1].")
    primary_citation: str = Field(
        description=(
            "Most important source label supporting the answer, or NONE only when evidence is "
            "insufficient."
        )
    )
    citations: list[str] = Field(
        default_factory=list,
        description="Any additional source labels used in the answer, and no unused labels.",
    )
    insufficient_evidence: bool = Field(
        default=False,
        description="True when the supplied project evidence cannot support a reliable answer.",
    )
