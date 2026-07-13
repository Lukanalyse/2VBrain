import re
from pathlib import Path

from schemas.linking import LinkableObject, LinkableType
from schemas.research_explorer import CorpusEntry, ExplorerObjectDetail
from services.linking_engine import LinkingEngine, LinkingEngineError


class ResearchExplorerError(Exception):
    pass


DESCRIPTION_SECTION_BY_TYPE: dict[LinkableType, str] = {
    LinkableType.paper: "Abstract",
    LinkableType.concept: "Description",
    LinkableType.project: "Overview",
    LinkableType.brainstorm: "Questions",
    LinkableType.review: "Overview",
    LinkableType.note: "Notes",
}

CORPUS_ROLES = [
    "Core",
    "Background",
    "Method",
    "Survey",
    "Application",
    "To Read",
    "Reading",
    "Paused",
    "Reviewed",
    "Cited",
]


class ResearchExplorer:
    """Read-only exploration layer for existing Markdown knowledge objects."""

    def __init__(self, linking_engine: LinkingEngine) -> None:
        self._linking_engine = linking_engine

    def search(self, query: str = "", object_types: list[LinkableType] | None = None) -> list[LinkableObject]:
        return self._linking_engine.search(query, object_types)

    def get_detail(self, object_id: str) -> ExplorerObjectDetail:
        try:
            relations = self._linking_engine.get_relations(object_id)
        except LinkingEngineError as error:
            raise ResearchExplorerError(str(error)) from error

        source = relations.source
        content = self._read_text(Path(source.markdown_path))
        metadata = self._frontmatter(content)
        related = {key: self._sort_objects(value) for key, value in relations.outgoing.items()}
        backlinks = {key: self._sort_objects(value) for key, value in relations.incoming.items()}
        all_related = self._unique_objects(
            [item for group in related.values() for item in group]
            + [item for group in backlinks.values() for item in group]
        )

        return ExplorerObjectDetail(
            object=source,
            description=self._description(source.type, content, metadata),
            parent=self._parent(source),
            tags=self._tags(metadata),
            metadata=metadata,
            related=related,
            backlinks=backlinks,
            all_related=all_related,
            corpus=self._corpus(source, content, all_related),
        )

    def _description(self, object_type: LinkableType, content: str, metadata: dict[str, str]) -> str:
        for key in ("abstract", "description", "title"):
            value = metadata.get(key, "").strip().strip('"')
            if key != "title" and value:
                return value

        section_name = DESCRIPTION_SECTION_BY_TYPE[object_type]
        section = self._extract_section(content, section_name).strip()
        return section.splitlines()[0].strip() if section else ""

    def _parent(self, item: LinkableObject) -> str:
        path = Path(item.markdown_path)
        return path.parent.name

    def _tags(self, metadata: dict[str, str]) -> list[str]:
        raw = metadata.get("tags", "")
        raw = raw.strip().strip("[]")
        return [tag.strip().strip('"') for tag in raw.split(",") if tag.strip()]

    def _frontmatter(self, content: str) -> dict[str, str]:
        if not content.startswith("---"):
            return {}
        match = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return {}
        metadata: dict[str, str] = {}
        current_list_key: str | None = None
        list_values: list[str] = []

        def flush() -> None:
            nonlocal current_list_key, list_values
            if current_list_key is not None:
                metadata[current_list_key] = ", ".join(list_values)
                current_list_key = None
                list_values = []

        for line in match.group(1).splitlines():
            stripped = line.strip()
            # Obsidian writes multi-value properties (e.g. tags) as a YAML block
            # list. Collect the indented "- item" lines under the pending key.
            if current_list_key is not None and stripped.startswith("- "):
                list_values.append(stripped[2:].strip().strip('"'))
                continue
            flush()
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value == "":
                # An empty value may be a scalar or the head of a block list;
                # defer so following "- item" lines can attach to this key.
                current_list_key = key
                metadata[key] = ""
            else:
                metadata[key] = value
        flush()
        return metadata

    def _extract_section(self, content: str, heading: str) -> str:
        pattern = rf"^# {re.escape(heading)}\s*$([\s\S]*?)(?=^# |\Z)"
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1) if match else ""

    def _corpus(
        self,
        source: LinkableObject,
        source_content: str,
        objects: list[LinkableObject],
    ) -> dict[LinkableType, list[CorpusEntry]]:
        if source.type not in {LinkableType.project, LinkableType.review}:
            return {object_type: [] for object_type in LinkableType}

        corpus = {object_type: [] for object_type in LinkableType}
        for item in objects:
            roles = self._corpus_roles(source_content, item)
            corpus[item.type].append(CorpusEntry(object=item, roles=roles))
        return {key: value for key, value in corpus.items() if value}

    def _corpus_roles(self, source_content: str, item: LinkableObject) -> list[str]:
        roles = set(self._explicit_roles(source_content, item))
        if item.type == LinkableType.paper:
            roles.update(self._paper_status_roles(item))
            roles.update(self._paper_semantic_roles(item))
        return sorted(roles, key=self._role_order)

    def _explicit_roles(self, content: str, item: LinkableObject) -> set[str]:
        roles = set()
        current_heading = ""
        labels = {Path(item.markdown_path).stem, item.title}
        for line in content.splitlines():
            heading_match = re.match(r"^#+\s+(.+?)\s*$", line)
            if heading_match:
                current_heading = heading_match.group(1)
            if not self._line_links_item(line, labels):
                continue
            searchable = f"{current_heading} {line}".lower()
            for role in CORPUS_ROLES:
                if re.search(rf"(^|[^a-z]){re.escape(role.lower())}([^a-z]|$)", searchable):
                    roles.add(role)
        return roles

    def _paper_status_roles(self, item: LinkableObject) -> set[str]:
        content = self._read_text(Path(item.markdown_path))
        metadata = self._frontmatter(content)
        status = metadata.get("status", "").strip().lower().replace("-", "_").replace(" ", "_")
        if status in {"unread", "to_read"}:
            return {"To Read"}
        if status == "reading":
            return {"Reading"}
        if status == "paused":
            return {"Paused"}
        if status in {"reviewed", "mastered"}:
            return {"Reviewed"}
        if status == "cited":
            return {"Cited"}
        return set()

    def _paper_semantic_roles(self, item: LinkableObject) -> set[str]:
        content = self._read_text(Path(item.markdown_path))
        metadata = self._frontmatter(content)
        text = " ".join(
            [
                item.title,
                metadata.get("title", ""),
                metadata.get("keywords", ""),
                metadata.get("journal", ""),
                metadata.get("conference", ""),
            ]
        ).lower()
        roles = set()
        if "survey" in text or "review" in text:
            roles.add("Survey")
        if any(token in text for token in ("method", "algorithm", "ucb", "thompson", "bayes", "regret")):
            roles.add("Method")
        if any(token in text for token in ("application", "clinical", "recommender", "online advertising")):
            roles.add("Application")
        return roles

    def _line_links_item(self, line: str, labels: set[str]) -> bool:
        linked_labels = {
            raw.split("|", 1)[0].split("#", 1)[0].strip().lower()
            for raw in re.findall(r"\[\[([^\]]+)\]\]", line)
        }
        return bool(linked_labels & {label.strip().lower() for label in labels})

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return ""

    def _role_order(self, role: str) -> int:
        try:
            return CORPUS_ROLES.index(role)
        except ValueError:
            return len(CORPUS_ROLES)

    def _sort_objects(self, objects: list[LinkableObject]) -> list[LinkableObject]:
        return sorted(objects, key=lambda item: (item.type.value, item.title.lower()))

    def _unique_objects(self, objects: list[LinkableObject]) -> list[LinkableObject]:
        seen: set[str] = set()
        unique: list[LinkableObject] = []
        for item in self._sort_objects(objects):
            if item.id in seen:
                continue
            seen.add(item.id)
            unique.append(item)
        return unique
