from typing import Literal

from pydantic import BaseModel, Field

from schemas.linking import LinkableObject


class WorkspaceObjectCreate(BaseModel):
    title: str
    color: str | None = None


class WorkspaceObjectDetail(BaseModel):
    object: LinkableObject
    content: str


class WorkspaceObjectList(BaseModel):
    objects: list[LinkableObject]


class WorkspaceMarkdownDocument(BaseModel):
    object: LinkableObject
    content: str


class WorkspaceMarkdownUpdate(BaseModel):
    content: str


class WorkspaceNote(BaseModel):
    id: str
    title: str
    path: str
    is_primary: bool = False


class WorkspaceNoteList(BaseModel):
    object: LinkableObject
    notes: list[WorkspaceNote]


class WorkspaceNoteDocument(BaseModel):
    object: LinkableObject
    note: WorkspaceNote
    content: str


class WorkspaceNoteCreate(BaseModel):
    title: str


class WorkspaceNoteRename(BaseModel):
    title: str


class WorkspaceStatusUpdate(BaseModel):
    status: str


class WorkspaceStatusResponse(BaseModel):
    object: LinkableObject
    status: str


class WorkspaceCollectionUpdate(BaseModel):
    collection_status: str


class WorkspaceCollectionResponse(BaseModel):
    object: LinkableObject
    collection_status: str


class WorkspaceProjectUpdate(BaseModel):
    project_id: str


class WorkspaceProjectResponse(BaseModel):
    object: LinkableObject
    project_id: str


class WorkspaceResearchMetadataUpdate(BaseModel):
    status: str = "unread"
    reading_progress: int = 0
    importance: str = ""
    priority: str = ""
    domain: str = ""
    method: str = ""
    difficulty: str = ""
    personal_tags: str = ""


class WorkspaceResearchMetadataResponse(BaseModel):
    object: LinkableObject
    metadata: dict[str, str | int | None]


class WorkspaceTagsUpdate(BaseModel):
    tags: list[str] = []


class WorkspaceTagsResponse(BaseModel):
    object: LinkableObject
    tags: list[str]


class WorkspaceRenameUpdate(BaseModel):
    title: str


class WorkspaceObjectResponse(BaseModel):
    object: LinkableObject


class WorkspaceColorUpdate(BaseModel):
    color: str


class HomeSummary(BaseModel):
    continue_reading: list[LinkableObject]
    recent_papers: list[LinkableObject]
    recent_concepts: list[LinkableObject]
    recent_brainstorm: list[LinkableObject]
    projects: list[LinkableObject]


class ActiveWorkspaceSummary(BaseModel):
    reading: list[LinkableObject]
    writing: list[LinkableObject]
    projects: list[LinkableObject]
    brainstorms: list[LinkableObject]


class PdfHighlightRect(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(gt=0, le=1)
    height: float = Field(gt=0, le=1)


class PdfHighlight(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    page: int = Field(ge=1)
    color: Literal["yellow", "green", "blue", "pink", "violet"]
    text: str = Field(max_length=50000)
    rects: list[PdfHighlightRect] = Field(min_length=1, max_length=2000)


class PdfHighlights(BaseModel):
    highlights: list[PdfHighlight] = Field(default_factory=list, max_length=10000)
