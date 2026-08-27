import re
from dataclasses import dataclass
from pathlib import Path
from threading import RLock

from repositories.library_repository import LibraryRepository
from schemas.linking import LinkableObject, LinkableType, ObjectRelations
from services.concept_manager import ConceptManager
from services.vault_manager import VaultManager


class LinkingEngineError(Exception):
    pass


@dataclass(frozen=True)
class _CatalogEntry:
    signature: tuple[object, ...]
    objects: tuple[LinkableObject, ...]


_CACHE_LOCK = RLock()
_CATALOG_CACHE: dict[str, _CatalogEntry] = {}
_TEXT_CACHE: dict[str, tuple[int, int, str]] = {}


SECTION_BY_TYPE: dict[LinkableType, str] = {
    LinkableType.paper: "Related Papers",
    LinkableType.concept: "Related Concepts",
    LinkableType.project: "Related Projects",
    LinkableType.brainstorm: "Brainstorm",
    LinkableType.review: "Literature Reviews",
    LinkableType.note: "Related Notes",
}

SECTION_ALIASES_BY_TYPE: dict[LinkableType, tuple[str, ...]] = {
    LinkableType.paper: ("Related Papers", "Papers", "Corpus"),
    LinkableType.concept: ("Related Concepts", "Concepts", "Themes"),
    LinkableType.project: ("Related Projects", "Projects"),
    LinkableType.brainstorm: ("Brainstorm", "Brainstorms"),
    LinkableType.review: ("Literature Reviews", "Reviews"),
    LinkableType.note: ("Related Notes", "Notes"),
}


class LinkingEngine:
    """Universal Markdown link manager. SQLite is used only to discover indexed papers."""

    def __init__(
        self,
        *,
        vault_manager: VaultManager,
        library_repository: LibraryRepository,
        concept_manager: ConceptManager,
    ) -> None:
        self._vault_manager = vault_manager
        self._library_repository = library_repository
        self._concept_manager = concept_manager
        self._objects_cache: list[LinkableObject] | None = None
        self._relation_cache: (
            dict[str, tuple[list[LinkableObject], list[LinkableObject]]] | None
        ) = None

    def search(
        self, query: str = "", object_types: list[LinkableType] | None = None
    ) -> list[LinkableObject]:
        normalized = query.strip().lower()
        allowed = set(object_types or list(LinkableType))
        objects = [item for item in self._objects() if item.type in allowed]
        if normalized:
            ranked = []
            for item in objects:
                match_score, excerpt = self._search_match(item, normalized)
                if match_score is not None:
                    ranked.append(
                        (match_score, item.model_copy(update={"search_excerpt": excerpt}))
                    )
            return [
                item
                for _, item in sorted(
                    ranked,
                    key=lambda entry: (entry[0], entry[1].type.value, entry[1].title.lower()),
                )
            ]
        return sorted(objects, key=lambda item: (item.type.value, item.title.lower()))

    def get_relations(self, source_id: str) -> ObjectRelations:
        source = self._get_object(source_id)
        relations = self._relation_index()
        outgoing = self._empty_groups()
        incoming = self._empty_groups()

        outgoing_items, incoming_items = relations.get(source_id, ([], []))
        for target in outgoing_items:
            outgoing[target.type].append(target)
        for candidate in incoming_items:
            incoming[candidate.type].append(candidate)

        return ObjectRelations(source=source, outgoing=outgoing, incoming=incoming)

    def link(self, source_id: str, target_ids: list[str]) -> list[LinkableObject]:
        source = self._get_object(source_id)
        targets = []
        for target_id in target_ids:
            target = self._get_object(target_id)
            if target.id != source.id and target.id not in {item.id for item in targets}:
                targets.append(target)

        path = Path(source.markdown_path)
        content = path.read_text(encoding="utf-8")
        for target in targets:
            section = self._preferred_section(content, target.type)
            existing_links = self._extract_section_links(content, section)
            link_label = self._link_label(target)
            if not self._has_link(content, target):
                existing_links.append(link_label)
                body = "\n".join(f"- [[{label}]]" for label in sorted(existing_links))
                content = self._replace_section(content, section, body)

        path.write_text(content, encoding="utf-8")
        self.invalidate_path(path)
        return targets

    def warm(self) -> tuple[int, int]:
        """Populate the object, Markdown and relation caches before the UI opens."""
        objects = self._objects()
        relations = self._relation_index()
        edge_count = sum(len(outgoing) for outgoing, _ in relations.values())
        return len(objects), edge_count

    def invalidate_path(self, path: Path) -> None:
        resolved = str(path.expanduser().resolve(strict=False))
        with _CACHE_LOCK:
            _TEXT_CACHE.pop(resolved, None)
        self._relation_cache = None

    def _objects(self) -> list[LinkableObject]:
        if self._objects_cache is not None:
            return self._objects_cache

        paper_objects = self._paper_objects()
        vault_root = self._vault_path()
        signature = self._catalog_signature(vault_root, paper_objects)
        cache_key = str(vault_root.expanduser().resolve(strict=False))
        with _CACHE_LOCK:
            cached = _CATALOG_CACHE.get(cache_key)
            if cached is not None and cached.signature == signature:
                self._objects_cache = list(cached.objects)
                return self._objects_cache

        base = [
            *paper_objects,
            *self._concept_objects(),
            *self._markdown_objects(LinkableType.project, "01 Projects", "Project"),
            *self._markdown_objects(LinkableType.brainstorm, "04 Brainstorm", "Brainstorm"),
            *self._markdown_objects(
                LinkableType.review, "05 Literature Reviews", "Literature Review"
            ),
        ]
        objects = [*base, *self._note_objects(base)]
        with _CACHE_LOCK:
            _CATALOG_CACHE[cache_key] = _CatalogEntry(
                signature=signature, objects=tuple(objects)
            )
        self._objects_cache = objects
        return objects

    def _catalog_signature(
        self, vault_root: Path, paper_objects: list[LinkableObject]
    ) -> tuple[object, ...]:
        paper_signature = tuple(
            (
                item.id,
                item.title,
                item.subtitle,
                item.markdown_path,
                item.collection_status,
                item.project_id,
            )
            for item in paper_objects
        )
        markdown_signature: list[tuple[str, int, int]] = []
        try:
            paths = vault_root.rglob("*.md")
            for path in paths:
                try:
                    stat = path.stat()
                    relative = str(path.relative_to(vault_root))
                    markdown_signature.append((relative, stat.st_mtime_ns, stat.st_size))
                except OSError:
                    continue
        except OSError:
            pass
        return paper_signature, tuple(sorted(markdown_signature))

    def _note_objects(self, parents: list[LinkableObject]) -> list[LinkableObject]:
        """Secondary notes (files in `<object>.notes/`) as first-class objects.
        The object's own markdown is its primary note and is not duplicated here.
        """
        notes: list[LinkableObject] = []
        for parent in parents:
            parent_path = Path(parent.markdown_path)
            notes_dir = parent_path.parent / f"{parent_path.stem}.notes"
            if not notes_dir.is_dir():
                continue
            for note_path in sorted(notes_dir.glob("*.md")):
                notes.append(
                    LinkableObject(
                        id=f"note:{parent_path.stem}::{note_path.stem}",
                        type=LinkableType.note,
                        title=note_path.stem,
                        subtitle=parent.title,
                        markdown_path=str(note_path),
                    )
                )
        return notes

    def _paper_objects(self) -> list[LinkableObject]:
        objects = []
        for item in self._library_repository.list_items():
            title = item.title or Path(item.markdown_path).stem
            objects.append(
                LinkableObject(
                    id=f"paper:{item.id}",
                    type=LinkableType.paper,
                    title=title,
                    subtitle=item.filename,
                    markdown_path=item.markdown_path,
                    collection_status=item.collection_status,
                    project_id=item.project_id,
                )
            )
        return objects

    def _concept_objects(self) -> list[LinkableObject]:
        return [
            LinkableObject(
                id=f"concept:{concept.slug}",
                type=LinkableType.concept,
                title=concept.name,
                subtitle=concept.category or "Concept",
                markdown_path=concept.markdown_path,
            )
            for concept in self._concept_manager.list_concepts(include_link_counts=False)
        ]

    def _markdown_objects(
        self, object_type: LinkableType, directory_name: str, subtitle: str
    ) -> list[LinkableObject]:
        directory = self._vault_path() / directory_name
        if not directory.exists():
            return []
        return [
            LinkableObject(
                id=f"{object_type.value}:{path.stem}",
                type=object_type,
                title=path.stem,
                subtitle=subtitle,
                markdown_path=str(path),
            )
            for path in sorted(directory.glob("*.md"))
        ]

    def _get_object(self, object_id: str) -> LinkableObject:
        for item in self._objects():
            if item.id == object_id:
                return item
        raise LinkingEngineError("Object not found.")

    def _vault_path(self) -> Path:
        status = self._vault_manager.get_storage_status()
        if not status.is_configured or status.vault_path is None:
            raise LinkingEngineError(
                "Configure a valid Obsidian vault before linking knowledge objects."
            )
        return status.vault_path

    def _empty_groups(self) -> dict[LinkableType, list[LinkableObject]]:
        return {object_type: [] for object_type in LinkableType}

    def _link_label(self, item: LinkableObject) -> str:
        return Path(item.markdown_path).stem

    def _has_link(self, content: str, target: LinkableObject) -> bool:
        labels = self._extract_wikilinks(content)
        target_labels = {self._link_label(target), target.title}
        return bool(labels & target_labels)

    def _object_lookup(self, objects: list[LinkableObject]) -> dict[str, LinkableObject]:
        lookup: dict[str, LinkableObject] = {}
        for item in objects:
            lookup[self._normalize_link_label(item.title)] = item
            lookup[self._normalize_link_label(self._link_label(item))] = item
        return lookup

    def _linked_objects(
        self, content: str, object_by_label: dict[str, LinkableObject]
    ) -> list[LinkableObject]:
        linked: list[LinkableObject] = []
        seen: set[str] = set()
        for label in self._extract_wikilinks(content):
            target = object_by_label.get(self._normalize_link_label(label))
            if target is None or target.id in seen:
                continue
            seen.add(target.id)
            linked.append(target)
        return linked

    def _extract_wikilinks(self, content: str) -> set[str]:
        links = set()
        for raw in re.findall(r"\[\[([^\]]+)\]\]", content):
            label = raw.split("|", 1)[0].split("#", 1)[0].strip()
            if label:
                links.add(label)
        return links

    def _normalize_link_label(self, label: str) -> str:
        return label.strip().lower()

    def _search_match(
        self, item: LinkableObject, normalized_query: str
    ) -> tuple[int, str] | tuple[None, str]:
        if normalized_query in item.title.lower():
            return 0, item.subtitle
        if normalized_query in item.subtitle.lower():
            return 1, item.subtitle

        content = self._read_text(Path(item.markdown_path))
        if normalized_query in content.lower():
            return 2, self._excerpt(content, normalized_query)

        notes_dir = self._notes_dir(item)
        if notes_dir.exists():
            for note_path in sorted(notes_dir.glob("*.md")):
                note_content = self._read_text(note_path)
                if normalized_query in note_content.lower():
                    note_excerpt = self._excerpt(note_content, normalized_query)
                    return 3, f"{note_path.stem}: {note_excerpt}"

        return None, ""

    def _read_text(self, path: Path) -> str:
        try:
            resolved = path.expanduser().resolve(strict=False)
            stat = resolved.stat()
        except OSError:
            return ""
        key = str(resolved)
        with _CACHE_LOCK:
            cached = _TEXT_CACHE.get(key)
            if cached is not None and cached[:2] == (stat.st_mtime_ns, stat.st_size):
                return cached[2]
        try:
            content = resolved.read_text(encoding="utf-8")
        except OSError:
            return ""
        with _CACHE_LOCK:
            _TEXT_CACHE[key] = (stat.st_mtime_ns, stat.st_size, content)
        return content

    def _relation_index(
        self,
    ) -> dict[str, tuple[list[LinkableObject], list[LinkableObject]]]:
        if self._relation_cache is not None:
            return self._relation_cache

        objects = self._objects()
        object_by_label = self._object_lookup(objects)
        outgoing_by_id: dict[str, list[LinkableObject]] = {
            item.id: [] for item in objects
        }
        incoming_by_id: dict[str, list[LinkableObject]] = {
            item.id: [] for item in objects
        }
        for source in objects:
            content = self._read_text(Path(source.markdown_path))
            targets = self._linked_objects(content, object_by_label)
            for target in targets:
                if target.id == source.id:
                    continue
                outgoing_by_id[source.id].append(target)
                incoming_by_id[target.id].append(source)

        self._relation_cache = {
            object_id: (
                sorted(outgoing_by_id[object_id], key=self._object_sort_key),
                sorted(incoming_by_id[object_id], key=self._object_sort_key),
            )
            for object_id in outgoing_by_id
        }
        return self._relation_cache

    @staticmethod
    def _object_sort_key(item: LinkableObject) -> tuple[str, str]:
        return item.type.value, item.title.lower()

    def _notes_dir(self, item: LinkableObject) -> Path:
        markdown_path = Path(item.markdown_path).expanduser().resolve()
        return markdown_path.parent / f"{markdown_path.stem}.notes"

    def _excerpt(self, content: str, normalized_query: str, radius: int = 96) -> str:
        compact = re.sub(r"\s+", " ", content).strip()
        index = compact.lower().find(normalized_query)
        if index < 0:
            return ""
        start = max(index - radius, 0)
        end = min(index + len(normalized_query) + radius, len(compact))
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(compact) else ""
        return f"{prefix}{compact[start:end].strip()}{suffix}"

    def _preferred_section(self, content: str, object_type: LinkableType) -> str:
        for heading in SECTION_ALIASES_BY_TYPE[object_type]:
            if self._has_section(content, heading):
                return heading
        return SECTION_BY_TYPE[object_type]

    def _has_section(self, content: str, heading: str) -> bool:
        pattern = rf"^# {re.escape(heading)}\s*$"
        return re.search(pattern, content, re.MULTILINE) is not None

    def _extract_section_links(self, content: str, heading: str) -> list[str]:
        section = self._extract_section(content, heading)
        return sorted(self._extract_wikilinks(section))

    def _extract_section(self, content: str, heading: str) -> str:
        pattern = rf"^# {re.escape(heading)}\s*$([\s\S]*?)(?=^# |\Z)"
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1) if match else ""

    def _replace_section(self, content: str, heading: str, body: str) -> str:
        section = f"# {heading}\n\n{body.strip()}\n\n"
        pattern = rf"^# {re.escape(heading)}\s*$[\s\S]*?(?=^# |\Z)"
        if re.search(pattern, content, re.MULTILINE):
            return re.sub(pattern, section, content, count=1, flags=re.MULTILINE)
        return f"{content.rstrip()}\n\n{section}"
