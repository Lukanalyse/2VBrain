import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

from repositories.library_repository import LibraryRepository
from schemas.linking import LinkableObject, LinkableType
from schemas.workspace import ActiveWorkspaceSummary, HomeSummary, WorkspaceNote
from services.concept_manager import ConceptManager
from services.linking_engine import LinkingEngine
from services.vault_manager import VaultManager


class WorkspaceManagerError(Exception):
    pass


READING_STATUSES = {"unread", "reading", "paused", "reviewed", "mastered"}
COLLECTION_STATUSES = {"inbox", "workspace", "library"}
PRIMARY_NOTE_ID = "primary"
PRIMARY_NOTE_TITLE = "Reading Note"


class WorkspaceManager:
    def __init__(
        self,
        *,
        vault_manager: VaultManager,
        library_repository: LibraryRepository,
        concept_manager: ConceptManager,
        linking_engine: LinkingEngine,
    ) -> None:
        self._vault_manager = vault_manager
        self._library_repository = library_repository
        self._concept_manager = concept_manager
        self._linking_engine = linking_engine

    def _vault_file(self, stored_path: str | Path) -> Path:
        """Resolve a stored vault path against the current runtime vault root."""
        return self._vault_manager.resolve_vault_file(stored_path)

    @staticmethod
    def _read_text_or_empty(path: Path) -> str:
        """Read a vault file, tolerating a missing or unreadable file."""
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return ""

    def home_summary(self) -> HomeSummary:
        papers = self._linking_engine.search("", [LinkableType.paper])
        workspace_papers = [paper for paper in papers if paper.collection_status == "workspace"]
        concepts = self._linking_engine.search("", [LinkableType.concept])
        brainstorm = self._linking_engine.search("", [LinkableType.brainstorm])
        projects = self._linking_engine.search("", [LinkableType.project])
        return HomeSummary(
            continue_reading=(workspace_papers or papers)[:3],
            recent_papers=papers[:6],
            recent_concepts=concepts[:6],
            recent_brainstorm=brainstorm[:5],
            projects=projects[:5],
        )

    def active_summary(self) -> ActiveWorkspaceSummary:
        papers = [
            paper
            for paper in self._linking_engine.search("", [LinkableType.paper])
            if paper.collection_status == "workspace"
        ]
        return ActiveWorkspaceSummary(
            reading=papers[:10],
            writing=self._linking_engine.search("", [LinkableType.review])[:10],
            projects=self._linking_engine.search("", [LinkableType.project])[:10],
            brainstorms=self._linking_engine.search("", [LinkableType.brainstorm])[:10],
        )

    def read_object_markdown(self, object_id: str) -> tuple[LinkableObject, str]:
        item = self._get_linkable_object(object_id)
        path = self._vault_file(item.markdown_path)
        # Tolerate a missing file (e.g. the note was deleted from the vault):
        # return empty content so the object still opens and can be re-created.
        return item, self._read_text_or_empty(path)

    def save_object_markdown(self, object_id: str, content: str) -> tuple[LinkableObject, str]:
        item = self._get_linkable_object(object_id)
        path = self._vault_file(item.markdown_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return item, content

    def list_object_notes(self, object_id: str) -> tuple[LinkableObject, list[WorkspaceNote]]:
        item = self._get_linkable_object(object_id)
        notes = [self._primary_note(item)]
        notes_dir = self._notes_dir(item)
        if notes_dir.exists():
            notes.extend(
                self._note_from_path(path, is_primary=False)
                for path in sorted(notes_dir.glob("*.md"), key=lambda entry: entry.stem.lower())
            )
        return item, notes

    def read_object_note(
        self, object_id: str, note_id: str
    ) -> tuple[LinkableObject, WorkspaceNote, str]:
        item = self._get_linkable_object(object_id)
        note = self._get_note(item, note_id)
        path = self._vault_file(note.path)
        return item, note, self._read_text_or_empty(path)

    def save_object_note(
        self,
        object_id: str,
        note_id: str,
        content: str,
    ) -> tuple[LinkableObject, WorkspaceNote, str]:
        item = self._get_linkable_object(object_id)
        note = self._get_note(item, note_id)
        path = self._vault_file(note.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return item, note, content

    def create_object_note(
        self,
        object_id: str,
        title: str,
    ) -> tuple[LinkableObject, WorkspaceNote, str]:
        item = self._get_linkable_object(object_id)
        clean_title = title.strip()
        if not clean_title:
            raise WorkspaceManagerError("Note title is required.")

        notes_dir = self._notes_dir(item)
        notes_dir.mkdir(parents=True, exist_ok=True)
        path = self._available_note_path(notes_dir, clean_title)
        content = self._note_template(clean_title, item)
        path.write_text(content, encoding="utf-8")
        return item, self._note_from_path(path, is_primary=False), content

    def rename_object_note(
        self,
        object_id: str,
        note_id: str,
        title: str,
    ) -> tuple[LinkableObject, WorkspaceNote]:
        item = self._get_linkable_object(object_id)
        clean_title = title.strip()
        if not clean_title:
            raise WorkspaceManagerError("Note title is required.")
        if note_id == PRIMARY_NOTE_ID:
            raise WorkspaceManagerError("The primary Reading Note cannot be renamed.")

        note = self._get_note(item, note_id)
        old_path = self._vault_file(note.path)
        requested_path = old_path.parent / f"{self._safe_filename(clean_title)}.md"
        new_path = (
            old_path
            if requested_path == old_path
            else self._available_note_path(old_path.parent, clean_title)
        )
        if old_path != new_path:
            old_path.rename(new_path)
        return item, self._note_from_path(new_path, is_primary=False)

    def delete_object_note(
        self, object_id: str, note_id: str
    ) -> tuple[LinkableObject, list[WorkspaceNote]]:
        item = self._get_linkable_object(object_id)
        if note_id == PRIMARY_NOTE_ID:
            raise WorkspaceManagerError("The primary Reading Note cannot be deleted.")
        note = self._get_note(item, note_id)
        path = self._vault_file(note.path)
        notes_dir = path.parent
        path.unlink()
        if notes_dir.exists() and not any(notes_dir.iterdir()):
            notes_dir.rmdir()
        return self.list_object_notes(object_id)

    def duplicate_object_note(
        self,
        object_id: str,
        note_id: str,
    ) -> tuple[LinkableObject, WorkspaceNote, str]:
        item, source_note, content = self.read_object_note(object_id, note_id)
        notes_dir = self._notes_dir(item)
        notes_dir.mkdir(parents=True, exist_ok=True)
        path = self._available_note_path(notes_dir, f"{source_note.title} Copy")
        path.write_text(content, encoding="utf-8")
        return item, self._note_from_path(path, is_primary=False), content

    def get_paper_pdf_path(self, object_id: str) -> Path:
        paper = self._get_library_item(object_id)
        path = self._vault_file(paper.file_path)
        if not path.exists():
            raise WorkspaceManagerError("PDF file not found.")
        return path

    def update_paper_status(
        self, object_id: str, reading_status: str
    ) -> tuple[LinkableObject, str]:
        normalized = reading_status.strip().lower()
        if normalized not in READING_STATUSES:
            raise WorkspaceManagerError("Unsupported reading status.")

        paper = self._library_repository.update_status(
            self._get_library_item(object_id), normalized
        )

        markdown_path = self._vault_file(paper.markdown_path)
        if markdown_path.exists():
            content = markdown_path.read_text(encoding="utf-8")
            markdown_path.write_text(
                self._replace_frontmatter_status(content, normalized), encoding="utf-8"
            )

        return self._paper_object(paper), normalized

    def update_paper_collection_status(
        self, object_id: str, collection_status: str
    ) -> tuple[LinkableObject, str]:
        normalized = collection_status.strip().lower()
        if normalized not in COLLECTION_STATUSES:
            raise WorkspaceManagerError("Unsupported collection status.")

        paper = self._library_repository.update_collection_status(
            self._get_library_item(object_id), normalized
        )

        markdown_path = self._vault_file(paper.markdown_path)
        if markdown_path.exists():
            content = markdown_path.read_text(encoding="utf-8")
            markdown_path.write_text(
                self._replace_frontmatter_collection(content, normalized),
                encoding="utf-8",
            )

        return self._paper_object(paper), normalized

    def set_paper_project(self, object_id: str, project_id: str) -> tuple[LinkableObject, str]:
        paper = self._get_library_item(object_id)
        project = self._get_linkable_object(project_id)
        if project.type != LinkableType.project:
            raise WorkspaceManagerError("Project id must reference a Project.")

        paper = self._library_repository.update_project_id(paper, project.id)

        markdown_path = self._vault_file(paper.markdown_path)
        if markdown_path.exists():
            content = markdown_path.read_text(encoding="utf-8")
            content = self._replace_frontmatter_value(content, "project_id", project.id)
            content = self._replace_frontmatter_value(content, "project", project.title)
            content = self._replace_project_section(content, project)
            markdown_path.write_text(content, encoding="utf-8")

        return self._paper_object(paper), project.id

    def update_paper_research_metadata(
        self,
        object_id: str,
        *,
        status: str,
        reading_progress: int,
        importance: str,
        priority: str,
        domain: str,
        method: str,
        difficulty: str,
        personal_tags: str,
    ) -> tuple[LinkableObject, dict[str, str | int | None]]:
        normalized_status = status.strip().lower()
        if normalized_status not in READING_STATUSES:
            raise WorkspaceManagerError("Unsupported reading status.")
        if reading_progress < 0 or reading_progress > 100:
            raise WorkspaceManagerError("Reading progress must be between 0 and 100.")

        paper = self._library_repository.update_research_metadata(
            self._get_library_item(object_id),
            status=normalized_status,
            reading_progress=reading_progress,
            importance=self._optional_text(importance),
            priority=self._optional_text(priority),
            domain=self._optional_text(domain),
            method=self._optional_text(method),
            difficulty=self._optional_text(difficulty),
            personal_tags=self._optional_text(personal_tags),
        )

        metadata = {
            "status": paper.status,
            "reading_progress": paper.reading_progress,
            "importance": paper.importance,
            "priority": paper.priority,
            "domain": paper.domain,
            "method": paper.method,
            "difficulty": paper.difficulty,
            "personal_tags": paper.personal_tags,
        }

        markdown_path = self._vault_file(paper.markdown_path)
        if markdown_path.exists():
            content = markdown_path.read_text(encoding="utf-8")
            content = self._replace_frontmatter_value(content, "status", paper.status)
            content = self._replace_frontmatter_value(
                content, "reading_progress", str(paper.reading_progress)
            )
            content = self._replace_frontmatter_value(content, "importance", paper.importance or "")
            content = self._replace_frontmatter_value(content, "priority", paper.priority or "")
            content = self._replace_frontmatter_value(content, "domain", paper.domain or "")
            content = self._replace_frontmatter_value(content, "method", paper.method or "")
            content = self._replace_frontmatter_value(content, "difficulty", paper.difficulty or "")
            content = self._replace_frontmatter_value(content, "tags", paper.personal_tags or "")
            markdown_path.write_text(content, encoding="utf-8")

        return self._paper_object(paper), metadata

    def set_object_tags(self, object_id: str, tags: list[str]) -> tuple[LinkableObject, list[str]]:
        """Set the `tags` frontmatter of any object (native, autosave-friendly).

        Works for every object type. For papers it also mirrors the value into
        the library DB so Library cards stay in sync.
        """
        cleaned = list(dict.fromkeys(tag.strip() for tag in tags if tag.strip()))

        if object_id.startswith("paper:"):
            item = self._get_library_item(object_id)
            paper = self._library_repository.update_research_metadata(
                item,
                status=item.status,
                reading_progress=item.reading_progress,
                importance=item.importance,
                priority=item.priority,
                domain=item.domain,
                method=item.method,
                difficulty=item.difficulty,
                personal_tags=", ".join(cleaned) or None,
            )
            obj = self._paper_object(paper)
        else:
            obj = self._get_linkable_object(object_id)

        markdown_path = self._vault_file(obj.markdown_path)
        if markdown_path.exists():
            content = markdown_path.read_text(encoding="utf-8")
            markdown_path.write_text(
                self._set_frontmatter_tags(content, cleaned), encoding="utf-8"
            )

        return obj, cleaned

    def delete_object(self, object_id: str) -> LinkableObject:
        """Delete any object: its markdown, its `.notes` folder, and (papers)
        the PDF plus the library DB row. Links pointing at it are left as
        harmless dangling references (reads tolerate missing files)."""
        if object_id.startswith("paper:"):
            item = self._get_library_item(object_id)
            obj = self._paper_object(item)
            markdown_path = self._vault_file(item.markdown_path)
            pdf_path = self._vault_file(item.file_path) if item.file_path else None
            self._library_repository.delete_item(item)
            self._delete_object_files(markdown_path, pdf_path)
        else:
            obj = self._get_linkable_object(object_id)
            self._delete_object_files(self._vault_file(obj.markdown_path))
        return obj

    def rename_object(self, object_id: str, new_title: str) -> LinkableObject:
        title = new_title.strip()
        if not title:
            raise WorkspaceManagerError("Title is required.")

        # Papers keep a stable id (paper:{db_id}); only the display title changes.
        if object_id.startswith("paper:"):
            item = self._get_library_item(object_id)
            paper = self._library_repository.update_title(item, title)
            markdown_path = self._vault_file(paper.markdown_path)
            if markdown_path.exists():
                content = markdown_path.read_text(encoding="utf-8")
                markdown_path.write_text(
                    self._replace_frontmatter_value(content, "title", title),
                    encoding="utf-8",
                )
            return self._paper_object(paper)

        # Markdown objects are identified by their filename stem, so a rename
        # renames the file, its `.notes` folder, and every [[wikilink]] to it.
        obj = self._get_linkable_object(object_id)
        old_path = self._vault_file(obj.markdown_path)
        old_stem = old_path.stem
        new_stem = self._safe_filename(title)
        if not new_stem:
            raise WorkspaceManagerError("Title is required.")
        new_path = old_path.with_name(f"{new_stem}.md")
        if new_path != old_path and new_path.exists():
            raise WorkspaceManagerError("An object with this name already exists.")

        if old_path.exists():
            content = self._replace_frontmatter_value(
                old_path.read_text(encoding="utf-8"), "title", title
            )
            old_path.write_text(content, encoding="utf-8")
            if new_path != old_path:
                old_path.rename(new_path)
                old_notes = old_path.parent / f"{old_stem}.notes"
                if old_notes.is_dir():
                    old_notes.rename(new_path.parent / f"{new_stem}.notes")
                self._rewrite_wikilinks(old_stem, new_stem)

        return self._object_by_markdown_path(new_path, obj.type, obj.subtitle or "")

    def duplicate_object(self, object_id: str) -> LinkableObject:
        if object_id.startswith("paper:"):
            raise WorkspaceManagerError("Papers cannot be duplicated.")
        obj = self._get_linkable_object(object_id)
        source = self._vault_file(obj.markdown_path)
        if not source.exists():
            raise WorkspaceManagerError("Object file not found.")
        base = self._safe_filename(f"{source.stem} copy")
        target = source.with_name(f"{base}.md")
        counter = 2
        while target.exists():
            target = source.with_name(f"{base} {counter}.md")
            counter += 1
        content = self._replace_frontmatter_value(
            source.read_text(encoding="utf-8"), "title", target.stem
        )
        target.write_text(content, encoding="utf-8")
        return self._object_by_markdown_path(target, obj.type, obj.subtitle or "")

    def _object_by_markdown_path(
        self, path: Path, fallback_type: LinkableType, fallback_subtitle: str
    ) -> LinkableObject:
        """Resolve the freshly written file to its indexed object so the id
        matches the engine's scheme (notes carry a `parent::stem` id)."""
        resolved = str(path.expanduser().resolve())
        for item in self._linking_engine.search(""):
            if str(self._vault_file(item.markdown_path)) == resolved:
                return item
        return self._object_from_path(path, fallback_type, fallback_subtitle)

    def _rewrite_wikilinks(self, old_stem: str, new_stem: str) -> None:
        if old_stem == new_stem:
            return
        pattern = re.compile(r"\[\[" + re.escape(old_stem) + r"(?P<rest>[\]|#])")
        for path in self._vault_path().rglob("*.md"):
            try:
                content = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if f"[[{old_stem}" not in content:
                continue
            updated = pattern.sub(lambda match: f"[[{new_stem}{match.group('rest')}", content)
            if updated != content:
                path.write_text(updated, encoding="utf-8")

    def _delete_object_files(self, markdown_path: Path, pdf_path: Path | None = None) -> None:
        for path in (markdown_path, pdf_path):
            if path is None:
                continue
            try:
                path.expanduser().unlink(missing_ok=True)
            except OSError:
                pass
        notes_dir = markdown_path.expanduser().parent / f"{markdown_path.stem}.notes"
        if notes_dir.is_dir():
            shutil.rmtree(notes_dir, ignore_errors=True)

    def list_projects(self) -> list[LinkableObject]:
        return self._linking_engine.search("", [LinkableType.project])

    def create_project(self, title: str) -> LinkableObject:
        path = self._create_markdown_note(
            directory="01 Projects",
            title=title,
            template=self._project_template(title),
        )
        return self._object_from_path(path, LinkableType.project, "Project")

    def get_project(self, slug: str) -> tuple[LinkableObject, str]:
        return self._get_markdown_object("01 Projects", slug, LinkableType.project, "Project")

    def list_brainstorm(self) -> list[LinkableObject]:
        return self._linking_engine.search("", [LinkableType.brainstorm])

    def create_brainstorm(self, title: str) -> LinkableObject:
        path = self._create_markdown_note(
            directory="04 Brainstorm",
            title=title,
            template=self._brainstorm_template(title),
        )
        return self._object_from_path(path, LinkableType.brainstorm, "Brainstorm")

    def get_brainstorm(self, slug: str) -> tuple[LinkableObject, str]:
        return self._get_markdown_object(
            "04 Brainstorm", slug, LinkableType.brainstorm, "Brainstorm"
        )

    def _create_markdown_note(self, *, directory: str, title: str, template: str) -> Path:
        clean_title = title.strip()
        if not clean_title:
            raise WorkspaceManagerError("Title is required.")

        target_dir = self._vault_path() / directory
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"{self._safe_filename(clean_title)}.md"
        if path.exists():
            raise WorkspaceManagerError("A note with this title already exists.")
        path.write_text(template, encoding="utf-8")
        return path

    def _get_markdown_object(
        self,
        directory: str,
        slug: str,
        object_type: LinkableType,
        subtitle: str,
    ) -> tuple[LinkableObject, str]:
        path = self._vault_path() / directory / f"{slug}.md"
        if not path.exists():
            raise WorkspaceManagerError("Workspace note not found.")
        return self._object_from_path(path, object_type, subtitle), path.read_text(encoding="utf-8")

    def _object_from_path(
        self, path: Path, object_type: LinkableType, subtitle: str
    ) -> LinkableObject:
        return LinkableObject(
            id=f"{object_type.value}:{path.stem}",
            type=object_type,
            title=path.stem,
            subtitle=subtitle,
            markdown_path=str(path),
        )

    def _get_linkable_object(self, object_id: str) -> LinkableObject:
        for item in self._linking_engine.search(""):
            if item.id == object_id:
                return item
        raise WorkspaceManagerError("Workspace object not found.")

    def _get_library_item(self, object_id: str):
        if not object_id.startswith("paper:"):
            raise WorkspaceManagerError("Only Paper objects have a PDF.")
        try:
            item_id = int(object_id.split(":", 1)[1])
        except ValueError as error:
            raise WorkspaceManagerError("Invalid Paper object id.") from error
        item = self._library_repository.get_by_id(item_id)
        if item is None:
            raise WorkspaceManagerError("Paper not found.")
        return item

    def _paper_object(self, item) -> LinkableObject:
        title = item.title or Path(item.markdown_path).stem
        return LinkableObject(
            id=f"paper:{item.id}",
            type=LinkableType.paper,
            title=title,
            subtitle=item.status,
            markdown_path=item.markdown_path,
            collection_status=item.collection_status,
            project_id=item.project_id,
        )

    def _replace_frontmatter_status(self, content: str, reading_status: str) -> str:
        if not content.startswith("---\n"):
            return content
        end = content.find("\n---", 4)
        if end == -1:
            return content
        frontmatter = content[4:end]
        if re.search(r"^status:\s*.*$", frontmatter, flags=re.MULTILINE):
            frontmatter = re.sub(
                r"^status:\s*.*$",
                f"status: {reading_status}",
                frontmatter,
                flags=re.MULTILINE,
            )
        else:
            frontmatter = f"{frontmatter}\nstatus: {reading_status}"
        return f"---\n{frontmatter}{content[end:]}"

    def _replace_frontmatter_collection(self, content: str, collection_status: str) -> str:
        if not content.startswith("---\n"):
            return content
        end = content.find("\n---", 4)
        if end == -1:
            return content
        frontmatter = content[4:end]
        if re.search(r"^collection:\s*.*$", frontmatter, flags=re.MULTILINE):
            frontmatter = re.sub(
                r"^collection:\s*.*$",
                f"collection: {collection_status}",
                frontmatter,
                flags=re.MULTILINE,
            )
        else:
            frontmatter = f"{frontmatter}\ncollection: {collection_status}"
        return f"---\n{frontmatter}{content[end:]}"

    def _replace_frontmatter_value(self, content: str, key: str, value: str) -> str:
        if not content.startswith("---\n"):
            return content
        end = content.find("\n---", 4)
        if end == -1:
            return content
        frontmatter = content[4:end]
        pattern = rf"^{re.escape(key)}:\s*.*$"
        if re.search(pattern, frontmatter, flags=re.MULTILINE):
            frontmatter = re.sub(
                pattern,
                f"{key}: {value}",
                frontmatter,
                flags=re.MULTILINE,
            )
        else:
            frontmatter = f"{frontmatter}\n{key}: {value}"
        return f"---\n{frontmatter}{content[end:]}"

    def _set_frontmatter_tags(self, content: str, tags: list[str]) -> str:
        """Write `tags: a, b` inline, replacing any prior scalar OR Obsidian
        block-list form (`tags:\n  - a`) so no orphan list items remain."""
        joined = ", ".join(tags)
        if not content.startswith("---\n"):
            return f"---\ntags: {joined}\n---\n\n{content}"
        end = content.find("\n---", 4)
        if end == -1:
            return content
        lines = content[4:end].split("\n")
        out: list[str] = []
        index = 0
        replaced = False
        while index < len(lines):
            line = lines[index]
            if re.match(r"^tags\s*:", line):
                index += 1
                # Drop any indented block-list items belonging to this key.
                while index < len(lines) and lines[index].lstrip().startswith("- "):
                    index += 1
                out.append(f"tags: {joined}")
                replaced = True
                continue
            out.append(line)
            index += 1
        if not replaced:
            out.append(f"tags: {joined}")
        new_frontmatter = "\n".join(out)
        return f"---\n{new_frontmatter}{content[end:]}"

    def _replace_project_section(self, content: str, project: LinkableObject) -> str:
        body = f"- [[{Path(project.markdown_path).stem}]]"
        for heading in ("Projects", "Related Projects"):
            if re.search(rf"^# {re.escape(heading)}\s*$", content, re.MULTILINE):
                return self._replace_section(content, heading, body)
        return self._replace_section(content, "Projects", body)

    def _replace_section(self, content: str, heading: str, body: str) -> str:
        section = f"# {heading}\n\n{body.strip()}\n\n"
        pattern = rf"^# {re.escape(heading)}\s*$[\s\S]*?(?=^# |\Z)"
        if re.search(pattern, content, re.MULTILINE):
            return re.sub(pattern, section, content, count=1, flags=re.MULTILINE)
        return f"{content.rstrip()}\n\n{section}"

    def _optional_text(self, value: str) -> str | None:
        stripped = value.strip()
        return stripped or None

    def _primary_note(self, item: LinkableObject) -> WorkspaceNote:
        return WorkspaceNote(
            id=PRIMARY_NOTE_ID,
            title=PRIMARY_NOTE_TITLE,
            path=item.markdown_path,
            is_primary=True,
        )

    def _notes_dir(self, item: LinkableObject) -> Path:
        markdown_path = self._vault_file(item.markdown_path)
        return markdown_path.parent / f"{markdown_path.stem}.notes"

    def _get_note(self, item: LinkableObject, note_id: str) -> WorkspaceNote:
        if note_id == PRIMARY_NOTE_ID:
            return self._primary_note(item)

        notes_dir = self._notes_dir(item)
        path = notes_dir / f"{note_id}.md"
        if not path.exists() or not path.is_file():
            raise WorkspaceManagerError("Workspace note not found.")
        return self._note_from_path(path, is_primary=False)

    def _note_from_path(self, path: Path, *, is_primary: bool) -> WorkspaceNote:
        return WorkspaceNote(
            id=PRIMARY_NOTE_ID if is_primary else path.stem,
            title=PRIMARY_NOTE_TITLE if is_primary else path.stem,
            path=str(path),
            is_primary=is_primary,
        )

    def _available_note_path(self, directory: Path, title: str) -> Path:
        stem = self._safe_filename(title)
        path = directory / f"{stem}.md"
        if not path.exists():
            return path

        index = 2
        while True:
            candidate = directory / f"{stem} {index}.md"
            if not candidate.exists():
                return candidate
            index += 1

    def _note_template(self, title: str, item: LinkableObject) -> str:
        now = datetime.now(UTC).isoformat()
        body = (
            "## Research Question\n\n"
            "## Core Contribution\n\n"
            "## Method\n\n"
            "## Key Results\n\n"
            "## Evidence and Quotations\n\n"
            "## Limitations\n\n"
            "## Use in My Research\n\n"
            "## Open Questions\n\n"
            if item.type == LinkableType.paper
            else ""
        )
        return (
            "---\n"
            f"title: {title}\n"
            f"parent: {item.title}\n"
            f"parent_id: {item.id}\n"
            f"created: {now}\n"
            f"updated: {now}\n"
            "---\n\n"
            f"# {title}\n\n"
            f"{body}"
        )

    def _vault_path(self) -> Path:
        status = self._vault_manager.get_storage_status()
        if not status.is_configured or status.vault_path is None:
            raise WorkspaceManagerError(
                "Configure a valid Obsidian vault before using the workspace."
            )
        return status.vault_path

    def _safe_filename(self, value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", value).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned or "Untitled"

    def _project_template(self, title: str) -> str:
        now = datetime.now(UTC).isoformat()
        return (
            "---\n"
            "type: project\n"
            f"title: {title}\n"
            f"created: {now}\n"
            f"updated: {now}\n"
            "---\n\n"
            "# Overview\n\n"
            "# Papers\n\n"
            "# Concepts\n\n"
            "# Brainstorm\n\n"
            "# Writing\n\n"
            "# Timeline\n\n"
            "# Tasks\n\n"
        )

    def _brainstorm_template(self, title: str) -> str:
        now = datetime.now(UTC).isoformat()
        return (
            "---\n"
            "type: brainstorm\n"
            f"title: {title}\n"
            f"created: {now}\n"
            f"updated: {now}\n"
            "---\n\n"
            "# Questions\n\n"
            "# Hypotheses\n\n"
            "# Decisions\n\n"
            "# Future Work\n\n"
            "# Related Papers\n\n"
            "# Related Concepts\n\n"
            "# Related Projects\n\n"
        )
