from pydantic import BaseModel

from schemas.concept import ConceptResponse
from schemas.library import LibraryItemResponse


class KnowledgeConceptSummary(BaseModel):
    concept: ConceptResponse
    description: str
    related_papers_count: int
    related_concepts_count: int
    related_projects_count: int


class KnowledgeExploreListResponse(BaseModel):
    concepts: list[KnowledgeConceptSummary]


class KnowledgeConceptView(BaseModel):
    concept: ConceptResponse
    description: str
    related_papers: list[LibraryItemResponse]
    related_concepts: list[ConceptResponse]
    related_projects: list[str]
    brainstorm_notes: list[str]


class ConceptConceptLinksUpdate(BaseModel):
    concept_names: list[str]


class ConceptConceptLinksResponse(BaseModel):
    concept_names: list[str]
