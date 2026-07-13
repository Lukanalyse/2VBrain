from pathlib import Path
from tempfile import SpooledTemporaryFile

from pypdf import PdfWriter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.settings import Settings
from database.base import Base
from repositories.library_repository import LibraryRepository
from schemas.concept import ConceptCreate
from services.concept_manager import ConceptManager
from services.library_manager import IncomingDocument, LibraryManager
from services.linking_engine import LinkingEngine
from services.research_explorer import ResearchExplorer
from services.vault_manager import VaultManager


def make_pdf(filename: str) -> IncomingDocument:
    file = SpooledTemporaryFile()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_metadata({"/Title": Path(filename).stem})
    writer.write(file)
    file.seek(0)
    return IncomingDocument(filename=filename, file=file, content_type="application/pdf")


def make_explorer(tmp_path: Path):
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
    repository = LibraryRepository(session)
    concept_manager = ConceptManager(vault_manager=vault_manager, library_repository=repository)
    linking_engine = LinkingEngine(
        vault_manager=vault_manager,
        library_repository=repository,
        concept_manager=concept_manager,
    )
    return (
        ResearchExplorer(linking_engine),
        LibraryManager(settings=settings, repository=repository, vault_manager=vault_manager),
        concept_manager,
        linking_engine,
    )


def test_research_explorer_returns_detail_and_related_objects(tmp_path: Path) -> None:
    explorer, library_manager, concept_manager, linking_engine = make_explorer(tmp_path)
    paper = library_manager.import_pdf(make_pdf("Explorer Paper.pdf"))
    concept = concept_manager.create_concept(
        ConceptCreate(
            name="Explorer Concept",
            description="Concept description",
            category="Method",
            tags=["explorer"],
        )
    )
    linking_engine.link(f"concept:{concept.slug}", [f"paper:{paper.id}"])

    detail = explorer.get_detail(f"concept:{concept.slug}")

    assert detail.object.title == "Explorer Concept"
    assert detail.description == "Concept description"
    assert detail.parent == "03 Knowledge"
    assert detail.tags == ["explorer"]
    assert [item.title for item in detail.related["paper"]] == ["Explorer Paper"]
    assert [item.title for item in detail.all_related] == ["Explorer Paper"]
