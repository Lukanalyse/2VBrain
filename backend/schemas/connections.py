from enum import StrEnum

from pydantic import BaseModel

from schemas.linking import LinkableObject


class ConnectionType(StrEnum):
    references = "references"
    related = "related"
    explains = "explains"
    uses = "uses"
    extends = "extends"
    contradicts = "contradicts"
    inspired_by = "inspired_by"


class ConnectionTypeDefinition(BaseModel):
    id: ConnectionType
    label: str
    description: str
    inverse_label: str
    weight: int = 1


class ConnectionCreate(BaseModel):
    target_id: str
    relation_type: ConnectionType = ConnectionType.related


class ConnectionResponse(BaseModel):
    id: str
    source: LinkableObject
    target: LinkableObject
    relation_type: ConnectionType


class ConnectionListResponse(BaseModel):
    current: LinkableObject
    outgoing: list[ConnectionResponse]
    incoming: list[ConnectionResponse]


class ConnectionSearchResponse(BaseModel):
    objects: list[LinkableObject]


class ConnectionTypesResponse(BaseModel):
    relation_types: list[ConnectionTypeDefinition]


class ConnectionGraphNode(BaseModel):
    id: str
    type: str
    title: str


class ConnectionGraphEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: ConnectionType


class ConnectionGraphResponse(BaseModel):
    nodes: list[ConnectionGraphNode]
    edges: list[ConnectionGraphEdge]
