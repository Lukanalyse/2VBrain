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
from services.literature_review_manager import LiteratureReviewManager
from services.vault_manager import VaultManager


def make_pdf(filename: str) -> IncomingDocument:
    file = SpooledTemporaryFile()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_metadata({"/Title": Path(filename).stem})
    writer.write(file)
    file.seek(0)
    return IncomingDocument(filename=filename, file=file, content_type="application/pdf")


def make_managers(tmp_path: Path):
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
        LiteratureReviewManager(vault_manager=vault_manager, linking_engine=linking_engine),
        LibraryManager(settings=settings, repository=repository, vault_manager=vault_manager),
        concept_manager,
        linking_engine,
    )


def test_literature_review_lifecycle_uses_markdown_as_source(tmp_path: Path) -> None:
    review_manager, library_manager, concept_manager, linking_engine = make_managers(tmp_path)
    first_paper = library_manager.import_pdf(make_pdf("Review Paper One.pdf"))
    second_paper = library_manager.import_pdf(make_pdf("Review Paper Two.pdf"))
    concept = concept_manager.create_concept(ConceptCreate(name="Review Concept"))

    review = review_manager.create_review("Multi Armed Bandits Review")
    review_path = Path(review.markdown_path)
    content = review_path.read_text(encoding="utf-8")

    assert review_path.exists()
    assert "# Overview" in content
    assert "# Open Questions" in content
    assert "# Writing" in content

    linking_engine.link(
        review.id,
        [f"paper:{first_paper.id}", f"paper:{second_paper.id}", f"concept:{concept.slug}"],
    )
    linked_content = review_path.read_text(encoding="utf-8")
    assert "[[Review Paper One]]" in linked_content
    assert "[[Review Paper Two]]" in linked_content
    assert "[[Review Concept]]" in linked_content

    updated = linked_content + "\nSynthesis paragraph.\n"
    _, saved = review_manager.save_review(review.title, updated)
    _, reopened = review_manager.get_review(review.title)

    assert "Synthesis paragraph." in saved
    assert reopened == saved
