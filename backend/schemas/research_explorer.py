from pydantic import BaseModel

from schemas.linking import LinkableObject, LinkableType


class ExplorerSearchResponse(BaseModel):
    objects: list[LinkableObject]


class CorpusEntry(BaseModel):
    object: LinkableObject
    roles: list[str] = []


class ExplorerObjectDetail(BaseModel):
    object: LinkableObject
    description: str = ""
    parent: str = ""
    tags: list[str] = []
    metadata: dict[str, str] = {}
    related: dict[LinkableType, list[LinkableObject]]
    backlinks: dict[LinkableType, list[LinkableObject]]
    all_related: list[LinkableObject]
    corpus: dict[LinkableType, list[CorpusEntry]] = {}
