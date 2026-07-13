import re
from datetime import UTC, datetime
from pathlib import Path

from schemas.linking import LinkableObject, LinkableType
from services.linking_engine import LinkingEngine
from services.vault_manager import VaultManager


class LiteratureReviewManagerError(Exception):
    pass


class LiteratureReviewManager:
    def __init__(self, *, vault_manager: VaultManager, linking_engine: LinkingEngine) -> None:
        self._vault_manager = vault_manager
        self._linking_engine = linking_engine

    def list_reviews(self) -> list[LinkableObject]:
        return self._linking_engine.search("", [LinkableType.review])

    def create_review(self, title: str) -> LinkableObject:
        clean_title = title.strip()
        if not clean_title:
            raise LiteratureReviewManagerError("Review title is required.")

        directory = self._reviews_dir()
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self._safe_filename(clean_title)}.md"
        if path.exists():
            raise LiteratureReviewManagerError("A Literature Review with this title already exists.")

        path.write_text(self._template(clean_title), encoding="utf-8")
        return self._review_from_path(path)

    def get_review(self, slug: str) -> tuple[LinkableObject, str]:
        path = self._reviews_dir() / f"{slug}.md"
        if not path.exists():
            raise LiteratureReviewManagerError("Literature Review not found.")
        return self._review_from_path(path), path.read_text(encoding="utf-8")

    def save_review(self, slug: str, content: str) -> tuple[LinkableObject, str]:
        path = self._reviews_dir() / f"{slug}.md"
        if not path.exists():
            raise LiteratureReviewManagerError("Literature Review not found.")
        path.write_text(content, encoding="utf-8")
        return self._review_from_path(path), content

    def _reviews_dir(self) -> Path:
        status = self._vault_manager.get_storage_status()
        if not status.is_configured or status.vault_path is None:
            raise LiteratureReviewManagerError(
                "Configure a valid Obsidian vault before managing Literature Reviews."
            )
        return status.vault_path / "05 Literature Reviews"

    def _review_from_path(self, path: Path) -> LinkableObject:
        return LinkableObject(
            id=f"review:{path.stem}",
            type=LinkableType.review,
            title=path.stem,
            subtitle="Literature Review",
            markdown_path=str(path),
        )

    def _safe_filename(self, value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", value).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned or "Untitled Literature Review"

    def _template(self, title: str) -> str:
        now = datetime.now(UTC).isoformat()
        return (
            "---\n"
            "type: literature_review\n"
            f"title: {title}\n"
            f"created: {now}\n"
            f"updated: {now}\n"
            "---\n\n"
            "# Overview\n\n"
            "# Papers\n\n"
            "# Concepts\n\n"
            "# Brainstorm\n\n"
            "# Open Questions\n\n"
            "# Writing\n\n"
            "# References\n\n"
        )
