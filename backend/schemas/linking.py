from enum import StrEnum

from pydantic import BaseModel


class LinkableType(StrEnum):
    paper = "paper"
    concept = "concept"
    project = "project"
    brainstorm = "brainstorm"
    review = "review"
    note = "note"


class LinkableObject(BaseModel):
    id: str
    type: LinkableType
    title: str
    subtitle: str = ""
    markdown_path: str
    search_excerpt: str = ""
    collection_status: str | None = None
    project_id: str | None = None


class LinkSearchResponse(BaseModel):
    objects: list[LinkableObject]


class LinkCreateRequest(BaseModel):
    target_ids: list[str]
    relation_type: str = "related_to"


class LinkCreateResponse(BaseModel):
    source: LinkableObject
    targets: list[LinkableObject]


class ObjectRelations(BaseModel):
    source: LinkableObject
    outgoing: dict[LinkableType, list[LinkableObject]]
    incoming: dict[LinkableType, list[LinkableObject]]
