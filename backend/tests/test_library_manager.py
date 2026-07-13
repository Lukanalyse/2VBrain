from pathlib import Path
from tempfile import SpooledTemporaryFile

from pypdf import PdfWriter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.settings import Settings
from database.base import Base
from models.library_item import LibraryItem
from repositories.library_repository import LibraryRepository
from schemas.library import DuplicateStrategy
from services.library_manager import (
    IncomingDocument,
    LibraryConflictError,
    LibraryImportError,
    LibraryManager,
)
from services.vault_manager import VaultManager


def make_pdf(filename: str = "Research Paper.pdf") -> IncomingDocument:
    file = SpooledTemporaryFile()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_metadata(
        {
            "/Title": "A Test Research Paper",
            "/Author": "Ada Lovelace, Alan Turing",
            "/Keywords": "testing, metadata",
        }
    )
    writer.write(file)
    file.seek(0)
    return IncomingDocument(filename=filename, file=file, content_type="application/pdf")


def make_manager(tmp_path: Path) -> LibraryManager:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", future=True)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, future=True)()

    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)

    settings = Settings(
        workspace_config_path=tmp_path / "workspace.json",
        library_path=tmp_path / "library",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
    )
    vault_manager = VaultManager(settings)
    vault_manager.save_vault_path(vault)

    return LibraryManager(
        settings=settings,
        repository=LibraryRepository(session),
        vault_manager=vault_manager,
    )


def test_import_pdf_creates_library_item_and_markdown_note(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)

    item = manager.import_pdf(make_pdf())

    assert isinstance(item, LibraryItem)
    assert item.filename == "Research Paper.pdf"
    assert item.title == "A Test Research Paper"
    assert item.authors == "Ada Lovelace, Alan Turing"
    assert Path(item.file_path).exists()
    assert Path(item.markdown_path).exists()
    markdown = Path(item.markdown_path).read_text(encoding="utf-8")
    assert 'title: "A Test Research Paper"' in markdown
    assert "# Abstract" in markdown


def test_import_pdf_detects_duplicate(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    manager.import_pdf(make_pdf())

    try:
        manager.import_pdf(make_pdf())
    except LibraryConflictError as error:
        assert "already been imported" in str(error)
    else:
        raise AssertionError("Expected duplicate import to raise LibraryConflictError")


def test_import_pdf_keep_both_creates_distinct_files(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    first = manager.import_pdf(make_pdf())
    second = manager.import_pdf(make_pdf(), duplicate_strategy=DuplicateStrategy.keep_both)

    assert first.filename == "Research Paper.pdf"
    assert second.filename == "Research Paper 2.pdf"
    assert Path(second.file_path).exists()


def test_preview_pdf_metadata_rejects_malformed_pdf(tmp_path: Path) -> None:
    manager = make_manager(tmp_path)
    file = SpooledTemporaryFile()
    file.write(b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n")
    file.seek(0)

    try:
        manager.preview_pdf_metadata(
            IncomingDocument(
                filename="Malformed.pdf",
                file=file,
                content_type="application/pdf",
            )
        )
    except LibraryImportError as error:
        assert "Unable to read PDF metadata" in str(error)
    else:
        raise AssertionError("Expected malformed PDF preview to raise LibraryImportError")
