from datetime import UTC, datetime
from pathlib import Path

from models.library_item import LibraryItem
from services.reader_manager import ReaderManager


def make_item(markdown_path: Path) -> LibraryItem:
    return LibraryItem(
        id=1,
        filename="Paper.pdf",
        original_filename="Paper.pdf",
        file_path=str(markdown_path.with_suffix(".pdf")),
        markdown_path=str(markdown_path),
        imported_at=datetime.now(UTC),
        status="unread",
    )


def test_reader_manager_reads_and_saves_markdown(tmp_path: Path) -> None:
    markdown_path = tmp_path / "Paper.md"
    markdown_path.write_text("# Notes\n\nInitial", encoding="utf-8")
    item = make_item(markdown_path)
    manager = ReaderManager()

    assert manager.read_markdown(item) == "# Notes\n\nInitial"

    manager.save_markdown(item, "# Notes\n\nUpdated")

    assert markdown_path.read_text(encoding="utf-8") == "# Notes\n\nUpdated"
