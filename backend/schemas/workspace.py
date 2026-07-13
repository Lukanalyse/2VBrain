from pydantic import BaseModel

from schemas.linking import LinkableObject


class WorkspaceObjectCreate(BaseModel):
    title: str


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
