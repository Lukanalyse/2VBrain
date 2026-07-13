from datetime import datetime

from pydantic import BaseModel

from schemas.library import LibraryItemResponse


class ConceptCreate(BaseModel):
    name: str
    description: str = ""
    category: str = ""
    tags: list[str] = []


class ConceptResponse(BaseModel):
    name: str
    slug: str
    category: str
    tags: list[str]
    markdown_path: str
    created: datetime | None = None
    updated: datetime | None = None
    linked_papers_count: int = 0
    linked_concepts_count: int = 0


class ConceptListResponse(BaseModel):
    concepts: list[ConceptResponse]


class ConceptDetailResponse(BaseModel):
    concept: ConceptResponse
    content: str
    linked_papers: list[LibraryItemResponse]


class PaperConceptLinksUpdate(BaseModel):
    concept_names: list[str]


class PaperConceptLinksResponse(BaseModel):
    concept_names: list[str]
