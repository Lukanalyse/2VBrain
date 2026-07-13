from pathlib import Path

from models.library_item import LibraryItem


class ReaderManagerError(Exception):
    pass


class ReaderManager:
    """Reads and writes Markdown notes. SQLite is never the source of note content."""

    def read_markdown(self, item: LibraryItem) -> str:
        markdown_path = self._resolve_markdown_path(item)
        if not markdown_path.exists():
            raise ReaderManagerError("Markdown note does not exist in the Vault.")

        return markdown_path.read_text(encoding="utf-8")

    def save_markdown(self, item: LibraryItem, content: str) -> str:
        markdown_path = self._resolve_markdown_path(item)
        if not markdown_path.parent.exists():
            raise ReaderManagerError("Markdown note folder does not exist in the Vault.")

        markdown_path.write_text(content, encoding="utf-8")
        return content

    def _resolve_markdown_path(self, item: LibraryItem) -> Path:
        return Path(item.markdown_path).expanduser().resolve()

