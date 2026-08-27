import re
from datetime import UTC, datetime
from pathlib import Path

from models.library_item import LibraryItem
from repositories.library_repository import LibraryRepository
from schemas.concept import ConceptCreate, ConceptResponse
from services.vault_manager import VaultManager


class ConceptManagerError(Exception):
    pass


class ConceptManager:
    def __init__(self, *, vault_manager: VaultManager, library_repository: LibraryRepository) -> None:
        self._vault_manager = vault_manager
        self._library_repository = library_repository

    def list_concepts(self, *, include_link_counts: bool = True) -> list[ConceptResponse]:
        concepts = [
            self._concept_from_path(path, include_link_counts=include_link_counts)
            for path in self._concepts_dir().glob("*.md")
        ]
        return sorted(concepts, key=lambda concept: concept.name.lower())

    def create_concept(self, payload: ConceptCreate) -> ConceptResponse:
        name = payload.name.strip()
        if not name:
            raise ConceptManagerError("Concept name is required.")

        concepts_dir = self._concepts_dir()
        concepts_dir.mkdir(parents=True, exist_ok=True)
        path = concepts_dir / f"{self._safe_filename(name)}.md"
        if path.exists():
            raise ConceptManagerError("Concept already exists.")

        now = datetime.now(UTC).isoformat()
        tags = ", ".join(payload.tags)
        path.write_text(
            "---\n"
            "type: concept\n"
            f"category: {payload.category}\n"
            f"tags: {tags}\n"
            f"created: {now}\n"
            f"updated: {now}\n"
            "---\n\n"
            "# Description\n\n"
            f"{payload.description}\n\n"
            "# Notes\n\n"
            "# Related Papers\n\n"
            "# Related Concepts\n\n"
            "# Related Projects\n\n"
            "# Brainstorm\n",
            encoding="utf-8",
        )

        return self._concept_from_path(path)

    def get_concept_detail(self, slug: str):
        path = self._concepts_dir() / f"{slug}.md"
        if not path.exists():
            raise ConceptManagerError("Concept not found.")

        concept = self._concept_from_path(path)
        linked_papers = self.get_linked_papers(concept.name)
        return concept, path.read_text(encoding="utf-8"), linked_papers

    def get_concept_content(self, slug: str) -> str:
        path = self._concepts_dir() / f"{slug}.md"
        if not path.exists():
            raise ConceptManagerError("Concept not found.")
        return path.read_text(encoding="utf-8")

    def link_related_concepts(self, slug: str, concept_names: list[str]) -> list[str]:
        path = self._concepts_dir() / f"{slug}.md"
        if not path.exists():
            raise ConceptManagerError("Concept not found.")

        current_name = path.stem
        available = {concept.name for concept in self.list_concepts()}
        clean_names = []
        for name in concept_names:
            clean = name.strip()
            if clean and clean != current_name and clean in available and clean not in clean_names:
                clean_names.append(clean)

        content = path.read_text(encoding="utf-8")
        replacement = "\n".join(f"- [[{name}]]" for name in clean_names)
        updated = self._replace_section(content, "Related Concepts", replacement)
        path.write_text(updated, encoding="utf-8")
        return clean_names

    def extract_section_links(self, content: str, heading: str) -> list[str]:
        section = self._extract_section(content, heading)
        return sorted(set(re.findall(r"\[\[([^\]]+)\]\]", section)))

    def extract_section_text(self, content: str, heading: str) -> str:
        return self._extract_section(content, heading)

    def get_linked_papers(self, concept_name: str) -> list[LibraryItem]:
        target = f"[[{concept_name}]]"
        papers: list[LibraryItem] = []
        for item in self._library_repository.list_items():
            markdown_path = Path(item.markdown_path).expanduser().resolve()
            if markdown_path.exists() and target in markdown_path.read_text(encoding="utf-8"):
                papers.append(item)
        return papers

    def get_paper_concepts(self, item: LibraryItem) -> list[str]:
        markdown_path = Path(item.markdown_path).expanduser().resolve()
        if not markdown_path.exists():
            raise ConceptManagerError("Paper Markdown note does not exist.")

        content = markdown_path.read_text(encoding="utf-8")
        section = self._extract_section(content, "Related Concepts")
        return sorted(set(re.findall(r"\[\[([^\]]+)\]\]", section)))

    def link_paper_concepts(self, item: LibraryItem, concept_names: list[str]) -> list[str]:
        available = {concept.name for concept in self.list_concepts()}
        clean_names = []
        for name in concept_names:
            clean = name.strip()
            if clean and clean in available and clean not in clean_names:
                clean_names.append(clean)

        markdown_path = Path(item.markdown_path).expanduser().resolve()
        if not markdown_path.exists():
            raise ConceptManagerError("Paper Markdown note does not exist.")

        content = markdown_path.read_text(encoding="utf-8")
        replacement = "\n".join(f"- [[{name}]]" for name in clean_names)
        updated = self._replace_section(content, "Related Concepts", replacement)
        markdown_path.write_text(updated, encoding="utf-8")
        return clean_names

    def _concepts_dir(self) -> Path:
        status = self._vault_manager.get_storage_status()
        if not status.is_configured or status.vault_path is None:
            raise ConceptManagerError("Configure a valid Obsidian vault before managing concepts.")
        return status.vault_path / "03 Knowledge"

    def _concept_from_path(
        self, path: Path, *, include_link_counts: bool = True
    ) -> ConceptResponse:
        content = path.read_text(encoding="utf-8")
        metadata = self._frontmatter(content)
        name = path.stem
        category = metadata.get("category", "")
        tags = [tag.strip() for tag in metadata.get("tags", "").split(",") if tag.strip()]
        linked_papers_count = len(self.get_linked_papers(name)) if include_link_counts else 0
        linked_concepts_count = (
            len(set(re.findall(r"\[\[([^\]]+)\]\]", content)))
            if include_link_counts
            else 0
        )

        return ConceptResponse(
            name=name,
            slug=path.stem,
            category=category,
            tags=tags,
            markdown_path=str(path),
            created=self._parse_datetime(metadata.get("created")),
            updated=self._parse_datetime(metadata.get("updated")),
            linked_papers_count=linked_papers_count,
            linked_concepts_count=linked_concepts_count,
        )

    def _frontmatter(self, content: str) -> dict[str, str]:
        if not content.startswith("---"):
            return {}
        match = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return {}
        metadata: dict[str, str] = {}
        for line in match.group(1).splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
        return metadata

    def _parse_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def _safe_filename(self, name: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", name).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned or "Untitled Concept"

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
