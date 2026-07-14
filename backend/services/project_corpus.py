from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from repositories.library_repository import LibraryRepository
from schemas.linking import LinkableObject, LinkableType
from services.linking_engine import LinkingEngine, LinkingEngineError
from services.vault_manager import VaultManager


class ProjectCorpusError(Exception):
    pass


@dataclass(frozen=True)
class ProjectSource:
    source_key: str
    object: LinkableObject
    source_kind: Literal["markdown", "pdf"]
    source_title: str
    path: Path


class ProjectCorpusResolver:
    """Builds the explicit one-hop source allow-list for one project."""

    def __init__(
        self,
        *,
        vault_manager: VaultManager,
        library_repository: LibraryRepository,
        linking_engine: LinkingEngine,
    ) -> None:
        self._vault_manager = vault_manager
        self._library_repository = library_repository
        self._linking_engine = linking_engine

    def resolve(self, project_id: str) -> list[ProjectSource]:
        project = self._project(project_id)
        try:
            relations = self._linking_engine.get_relations(project_id)
        except LinkingEngineError as error:
            raise ProjectCorpusError(str(error)) from error

        objects = [
            project,
            *(item for group in relations.outgoing.values() for item in group),
            *(item for group in relations.incoming.values() for item in group),
            *(
                paper
                for paper in self._linking_engine.search("", [LinkableType.paper])
                if paper.project_id == project_id
            ),
        ]
        unique_objects = {item.id: item for item in objects}

        sources: dict[str, ProjectSource] = {}
        for item in unique_objects.values():
            markdown_path = self._vault_manager.resolve_vault_file(item.markdown_path)
            self._add_source(
                sources,
                item=item,
                source_kind="markdown",
                source_title=item.title,
                path=markdown_path,
            )
            self._add_secondary_notes(sources, item, markdown_path)
            if item.type == LinkableType.paper:
                self._add_paper_pdf(sources, item)

        return sorted(sources.values(), key=lambda source: source.source_key)

    def _project(self, project_id: str) -> LinkableObject:
        for item in self._linking_engine.search("", [LinkableType.project]):
            if item.id == project_id:
                return item
        raise ProjectCorpusError("Project not found.")

    def _add_secondary_notes(
        self,
        sources: dict[str, ProjectSource],
        parent: LinkableObject,
        markdown_path: Path,
    ) -> None:
        notes_dir = markdown_path.parent / f"{markdown_path.stem}.notes"
        if not notes_dir.is_dir():
            return
        for note_path in sorted(notes_dir.glob("*.md")):
            note = LinkableObject(
                id=f"note:{markdown_path.stem}::{note_path.stem}",
                type=LinkableType.note,
                title=note_path.stem,
                subtitle=parent.title,
                markdown_path=str(note_path),
            )
            self._add_source(
                sources,
                item=note,
                source_kind="markdown",
                source_title=f"{parent.title} / {note.title}",
                path=note_path,
            )

    def _add_paper_pdf(self, sources: dict[str, ProjectSource], paper: LinkableObject) -> None:
        try:
            paper_id = int(paper.id.split(":", 1)[1])
        except (IndexError, ValueError):
            return
        item = self._library_repository.get_by_id(paper_id)
        if item is None:
            return
        self._add_source(
            sources,
            item=paper,
            source_kind="pdf",
            source_title=f"{paper.title} PDF",
            path=self._vault_manager.resolve_vault_file(item.file_path),
        )

    def _add_source(
        self,
        sources: dict[str, ProjectSource],
        *,
        item: LinkableObject,
        source_kind: Literal["markdown", "pdf"],
        source_title: str,
        path: Path,
    ) -> None:
        try:
            resolved = path.expanduser().resolve(strict=False)
        except OSError:
            return
        if not self._vault_manager.is_managed_content_path(resolved) or not resolved.is_file():
            return
        source_key = f"{source_kind}:{resolved}"
        sources[source_key] = ProjectSource(
            source_key=source_key,
            object=item,
            source_kind=source_kind,
            source_title=source_title,
            path=resolved,
        )
