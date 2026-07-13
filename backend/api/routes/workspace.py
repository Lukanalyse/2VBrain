import platform
import subprocess

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from core.settings import get_settings
from database.session import get_db
from repositories.library_repository import LibraryRepository
from schemas.workspace import (
    ActiveWorkspaceSummary,
    HomeSummary,
    WorkspaceCollectionResponse,
    WorkspaceCollectionUpdate,
    WorkspaceMarkdownDocument,
    WorkspaceMarkdownUpdate,
    WorkspaceNoteCreate,
    WorkspaceNoteDocument,
    WorkspaceNoteList,
    WorkspaceNoteRename,
    WorkspaceObjectCreate,
    WorkspaceObjectDetail,
    WorkspaceObjectList,
    WorkspaceProjectResponse,
    WorkspaceProjectUpdate,
    WorkspaceResearchMetadataResponse,
    WorkspaceResearchMetadataUpdate,
    WorkspaceObjectResponse,
    WorkspaceRenameUpdate,
    WorkspaceStatusResponse,
    WorkspaceStatusUpdate,
    WorkspaceTagsResponse,
    WorkspaceTagsUpdate,
)
from services.concept_manager import ConceptManager, ConceptManagerError
from services.linking_engine import LinkingEngine, LinkingEngineError
from services.vault_manager import VaultManager
from services.workspace_manager import WorkspaceManager, WorkspaceManagerError

router = APIRouter()


def get_workspace_manager(db: Session = Depends(get_db)) -> WorkspaceManager:
    settings = get_settings()
    repository = LibraryRepository(db)
    vault_manager = VaultManager(settings)
    concept_manager = ConceptManager(vault_manager=vault_manager, library_repository=repository)
    linking_engine = LinkingEngine(
        vault_manager=vault_manager,
        library_repository=repository,
        concept_manager=concept_manager,
    )
    return WorkspaceManager(
        vault_manager=vault_manager,
        library_repository=repository,
        concept_manager=concept_manager,
        linking_engine=linking_engine,
    )


@router.get("/home", response_model=HomeSummary)
def read_home(manager: WorkspaceManager = Depends(get_workspace_manager)) -> HomeSummary:
    try:
        return manager.home_summary()
    except (ConceptManagerError, LinkingEngineError, WorkspaceManagerError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/active", response_model=ActiveWorkspaceSummary)
def read_active_workspace(
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> ActiveWorkspaceSummary:
    try:
        return manager.active_summary()
    except (ConceptManagerError, LinkingEngineError, WorkspaceManagerError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/objects/{object_id}/markdown", response_model=WorkspaceMarkdownDocument)
def read_object_markdown(
    object_id: str,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceMarkdownDocument:
    try:
        item, content = manager.read_object_markdown(object_id)
        return WorkspaceMarkdownDocument(object=item, content=content)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.put("/objects/{object_id}/markdown", response_model=WorkspaceMarkdownDocument)
def save_object_markdown(
    object_id: str,
    payload: WorkspaceMarkdownUpdate,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceMarkdownDocument:
    try:
        item, content = manager.save_object_markdown(object_id, payload.content)
        return WorkspaceMarkdownDocument(object=item, content=content)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/objects/{object_id}/notes", response_model=WorkspaceNoteList)
def list_object_notes(
    object_id: str,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceNoteList:
    try:
        item, notes = manager.list_object_notes(object_id)
        return WorkspaceNoteList(object=item, notes=notes)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/objects/{object_id}/notes", response_model=WorkspaceNoteDocument)
def create_object_note(
    object_id: str,
    payload: WorkspaceNoteCreate,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceNoteDocument:
    try:
        item, note, content = manager.create_object_note(object_id, payload.title)
        return WorkspaceNoteDocument(object=item, note=note, content=content)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/objects/{object_id}/notes/{note_id}", response_model=WorkspaceNoteDocument)
def read_object_note(
    object_id: str,
    note_id: str,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceNoteDocument:
    try:
        item, note, content = manager.read_object_note(object_id, note_id)
        return WorkspaceNoteDocument(object=item, note=note, content=content)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.put("/objects/{object_id}/notes/{note_id}", response_model=WorkspaceNoteDocument)
def save_object_note(
    object_id: str,
    note_id: str,
    payload: WorkspaceMarkdownUpdate,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceNoteDocument:
    try:
        item, note, content = manager.save_object_note(object_id, note_id, payload.content)
        return WorkspaceNoteDocument(object=item, note=note, content=content)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.patch("/objects/{object_id}/notes/{note_id}", response_model=WorkspaceNoteDocument)
def rename_object_note(
    object_id: str,
    note_id: str,
    payload: WorkspaceNoteRename,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceNoteDocument:
    try:
        item, note = manager.rename_object_note(object_id, note_id, payload.title)
        _, _, content = manager.read_object_note(object_id, note.id)
        return WorkspaceNoteDocument(object=item, note=note, content=content)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post(
    "/objects/{object_id}/notes/{note_id}/duplicate",
    response_model=WorkspaceNoteDocument,
)
def duplicate_object_note(
    object_id: str,
    note_id: str,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceNoteDocument:
    try:
        item, note, content = manager.duplicate_object_note(object_id, note_id)
        return WorkspaceNoteDocument(object=item, note=note, content=content)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/objects/{object_id}/notes/{note_id}", response_model=WorkspaceNoteList)
def delete_object_note(
    object_id: str,
    note_id: str,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceNoteList:
    try:
        item, notes = manager.delete_object_note(object_id, note_id)
        return WorkspaceNoteList(object=item, notes=notes)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/objects/{object_id}/pdf")
def read_object_pdf(
    object_id: str,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> FileResponse:
    try:
        path = manager.get_paper_pdf_path(object_id)
        # inline so the browser renders the PDF in the opened tab instead of
        # forcing a download; filename is kept for the reader's "Save as".
        return FileResponse(
            path,
            media_type="application/pdf",
            filename=path.name,
            content_disposition_type="inline",
        )
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/objects/{object_id}/open-pdf")
def open_object_pdf(
    object_id: str,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> dict[str, str]:
    # Resolve the real PDF file on disk (its vault path, verified to exist by
    # get_paper_pdf_path) — never a temporary copy or an HTTP endpoint.
    try:
        path = manager.get_paper_pdf_path(object_id)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    # Opening a file in the desktop PDF app requires a process running on the
    # user's machine. Inside the headless Docker container there is no desktop
    # session, so refuse honestly instead of pretending to succeed.
    if get_settings().runtime_environment.lower() == "docker":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Research OS is running in Docker and cannot open the file in your "
                "desktop PDF app. Run the backend natively to open PDFs with your "
                "system reader, or open the file directly from your Obsidian vault."
            ),
        )

    # Hand the request to the OS default handler for the file's type.
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", str(path)])
        elif system == "Windows":
            subprocess.Popen(["cmd", "/c", "start", "", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not launch the system PDF viewer: {error}",
        ) from error

    return {"status": "opened", "path": str(path)}


@router.put("/objects/{object_id}/status", response_model=WorkspaceStatusResponse)
def update_object_status(
    object_id: str,
    payload: WorkspaceStatusUpdate,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceStatusResponse:
    try:
        item, reading_status = manager.update_paper_status(object_id, payload.status)
        return WorkspaceStatusResponse(object=item, status=reading_status)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.put("/objects/{object_id}/collection", response_model=WorkspaceCollectionResponse)
def update_object_collection(
    object_id: str,
    payload: WorkspaceCollectionUpdate,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceCollectionResponse:
    try:
        item, collection_status = manager.update_paper_collection_status(
            object_id, payload.collection_status
        )
        return WorkspaceCollectionResponse(
            object=item,
            collection_status=collection_status,
        )
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.put("/objects/{object_id}/project", response_model=WorkspaceProjectResponse)
def set_object_project(
    object_id: str,
    payload: WorkspaceProjectUpdate,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceProjectResponse:
    try:
        item, project_id = manager.set_paper_project(object_id, payload.project_id)
        return WorkspaceProjectResponse(object=item, project_id=project_id)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.put(
    "/objects/{object_id}/research-metadata",
    response_model=WorkspaceResearchMetadataResponse,
)
def update_object_research_metadata(
    object_id: str,
    payload: WorkspaceResearchMetadataUpdate,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceResearchMetadataResponse:
    try:
        item, metadata = manager.update_paper_research_metadata(
            object_id,
            status=payload.status,
            reading_progress=payload.reading_progress,
            importance=payload.importance,
            priority=payload.priority,
            domain=payload.domain,
            method=payload.method,
            difficulty=payload.difficulty,
            personal_tags=payload.personal_tags,
        )
        return WorkspaceResearchMetadataResponse(object=item, metadata=metadata)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.put("/objects/{object_id}/tags", response_model=WorkspaceTagsResponse)
def update_object_tags(
    object_id: str,
    payload: WorkspaceTagsUpdate,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceTagsResponse:
    try:
        item, tags = manager.set_object_tags(object_id, payload.tags)
        return WorkspaceTagsResponse(object=item, tags=tags)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/objects/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_object(
    object_id: str,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> None:
    try:
        manager.delete_object(object_id)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.put("/objects/{object_id}/rename", response_model=WorkspaceObjectResponse)
def rename_object(
    object_id: str,
    payload: WorkspaceRenameUpdate,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceObjectResponse:
    try:
        return WorkspaceObjectResponse(object=manager.rename_object(object_id, payload.title))
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/objects/{object_id}/duplicate", response_model=WorkspaceObjectResponse)
def duplicate_object(
    object_id: str,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceObjectResponse:
    try:
        return WorkspaceObjectResponse(object=manager.duplicate_object(object_id))
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/projects", response_model=WorkspaceObjectList)
def list_projects(
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceObjectList:
    return WorkspaceObjectList(objects=manager.list_projects())


@router.post("/projects", response_model=WorkspaceObjectDetail)
def create_project(
    payload: WorkspaceObjectCreate,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceObjectDetail:
    try:
        item = manager.create_project(payload.title)
        return WorkspaceObjectDetail(object=item, content="")
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/projects/{slug}", response_model=WorkspaceObjectDetail)
def read_project(
    slug: str,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceObjectDetail:
    try:
        item, content = manager.get_project(slug)
        return WorkspaceObjectDetail(object=item, content=content)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/brainstorm", response_model=WorkspaceObjectList)
def list_brainstorm(
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceObjectList:
    return WorkspaceObjectList(objects=manager.list_brainstorm())


@router.post("/brainstorm", response_model=WorkspaceObjectDetail)
def create_brainstorm(
    payload: WorkspaceObjectCreate,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceObjectDetail:
    try:
        item = manager.create_brainstorm(payload.title)
        return WorkspaceObjectDetail(object=item, content="")
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/brainstorm/{slug}", response_model=WorkspaceObjectDetail)
def read_brainstorm(
    slug: str,
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> WorkspaceObjectDetail:
    try:
        item, content = manager.get_brainstorm(slug)
        return WorkspaceObjectDetail(object=item, content=content)
    except WorkspaceManagerError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
