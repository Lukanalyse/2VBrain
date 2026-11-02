from pathlib import Path
from tempfile import SpooledTemporaryFile

from pypdf import PdfWriter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.settings import Settings
from database.base import Base
from repositories.library_repository import LibraryRepository
from schemas.concept import ConceptCreate
from schemas.linking import LinkableType
from services.concept_manager import ConceptManager
from services.library_manager import IncomingDocument, LibraryManager
from services.linking_engine import LinkingEngine
from services.vault_manager import VaultManager
from services.workspace_manager import WorkspaceManager


def make_pdf(filename: str) -> IncomingDocument:
    file = SpooledTemporaryFile()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_metadata({"/Title": Path(filename).stem})
    writer.write(file)
    file.seek(0)
    return IncomingDocument(filename=filename, file=file, content_type="application/pdf")


def make_engine(tmp_path: Path):
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

    return (
        LinkingEngine(
            vault_manager=vault_manager,
            library_repository=repository,
            concept_manager=concept_manager,
        ),
        LibraryManager(settings=settings, repository=repository, vault_manager=vault_manager),
        concept_manager,
        vault,
    )


def test_universal_linking_engine_writes_markdown_links(tmp_path: Path) -> None:
    engine, library_manager, concept_manager, vault = make_engine(tmp_path)
    first_paper = library_manager.import_pdf(make_pdf("Paper One.pdf"))
    second_paper = library_manager.import_pdf(make_pdf("Paper Two.pdf"))
    first_concept = concept_manager.create_concept(ConceptCreate(name="Bandits"))
    second_concept = concept_manager.create_concept(ConceptCreate(name="Bayesian Learning"))

    projects_dir = vault / "01 Projects"
    brainstorm_dir = vault / "04 Brainstorm"
    projects_dir.mkdir(parents=True)
    brainstorm_dir.mkdir(parents=True)
    project_path = projects_dir / "Doctorat.md"
    brainstorm_path = brainstorm_dir / "Ideas.md"
    project_path.write_text("# Notes\n", encoding="utf-8")
    brainstorm_path.write_text("# Notes\n", encoding="utf-8")

    engine.link(f"paper:{first_paper.id}", [f"paper:{second_paper.id}", f"concept:{first_concept.slug}"])
    engine.link(f"concept:{first_concept.slug}", ["project:Doctorat"])
    engine.link("brainstorm:Ideas", [f"concept:{first_concept.slug}", f"concept:{second_concept.slug}"])

    first_paper_markdown = Path(first_paper.markdown_path).read_text(encoding="utf-8")
    concept_markdown = Path(first_concept.markdown_path).read_text(encoding="utf-8")
    brainstorm_markdown = brainstorm_path.read_text(encoding="utf-8")

    assert "[[Paper Two]]" in first_paper_markdown
    assert "[[Bandits]]" in first_paper_markdown
    assert "[[Doctorat]]" in concept_markdown
    assert "[[Bandits]]" in brainstorm_markdown
    assert "[[Bayesian Learning]]" in brainstorm_markdown

    original_read_text = engine._read_text
    read_count = 0

    def counted_read_text(path: Path) -> str:
        nonlocal read_count
        read_count += 1
        return original_read_text(path)

    engine._read_text = counted_read_text
    paper_relations = engine.get_relations(f"paper:{first_paper.id}")
    reads_after_first_relation_lookup = read_count
    assert [item.title for item in paper_relations.outgoing["paper"]] == ["Paper Two"]
    assert [item.title for item in paper_relations.outgoing["concept"]] == ["Bandits"]

    concept_relations = engine.get_relations(f"concept:{first_concept.slug}")
    assert read_count == reads_after_first_relation_lookup
    assert [item.title for item in concept_relations.incoming["paper"]] == ["Paper One"]
    assert [item.title for item in concept_relations.incoming["brainstorm"]] == ["Ideas"]


def test_standalone_notes_are_indexed_with_color_and_can_link_to_projects(
    tmp_path: Path,
) -> None:
    engine, _, _, vault = make_engine(tmp_path)
    notes_dir = vault / "02 Notes"
    projects_dir = vault / "01 Projects"
    notes_dir.mkdir(parents=True)
    projects_dir.mkdir(parents=True)
    (notes_dir / "Data.md").write_text(
        "---\ntitle: Data\ntype: note\ncolor: violet\n---\n\nFree note.\n",
        encoding="utf-8",
    )
    (projects_dir / "MAB.md").write_text("# Notes\n", encoding="utf-8")

    notes = engine.search("", [LinkableType.note])
    assert [(item.id, item.title, item.color) for item in notes] == [
        ("note:Data", "Data", "violet")
    ]

    engine.link("note:Data", ["project:MAB"])
    relations = engine.get_relations("note:Data")
    assert [item.title for item in relations.outgoing["project"]] == ["MAB"]


def test_workspace_manager_creates_and_recolors_a_free_note(tmp_path: Path) -> None:
    engine, _, concept_manager, vault = make_engine(tmp_path)
    manager = WorkspaceManager(
        vault_manager=engine._vault_manager,
        library_repository=engine._library_repository,
        concept_manager=concept_manager,
        linking_engine=engine,
    )

    note = manager.create_note("Dataset", "teal")
    assert note.id == "note:Dataset"
    assert note.color == "teal"
    assert (vault / "02 Notes" / "Dataset.md").exists()

    recolored = manager.set_object_color(note.id, "amber")
    assert recolored.color == "amber"
    assert "color: amber" in (vault / "02 Notes" / "Dataset.md").read_text(
        encoding="utf-8"
    )


def test_pdf_highlights_persist_without_changing_original(tmp_path: Path) -> None:
    import pytest
    from schemas.workspace import PdfHighlight, PdfHighlights
    from services.workspace_manager import WorkspaceManagerError

    engine, library, concepts, _ = make_engine(tmp_path)
    paper = library.import_pdf(make_pdf("Highlighted.pdf"))
    manager = WorkspaceManager(
        vault_manager=engine._vault_manager,
        library_repository=engine._library_repository,
        concept_manager=concepts,
        linking_engine=engine,
    )
    object_id = f"paper:{paper.id}"
    original = Path(paper.file_path).read_bytes()
    assert manager.read_pdf_highlights(object_id).highlights == []
    mark = PdfHighlight(id="mark-1", page=1, color="pink", text="Selected text",
                        rects=[dict(x=0.1, y=0.2, width=0.3, height=0.02)])
    saved = PdfHighlights(highlights=[mark])
    manager.save_pdf_highlights(object_id, saved)
    assert manager.read_pdf_highlights(object_id) == saved
    assert Path(paper.file_path).read_bytes() == original
    with pytest.raises(WorkspaceManagerError, match="outside"):
        manager.save_pdf_highlights(object_id, PdfHighlights(
            highlights=[mark.model_copy(update={"page": 2})]))
    assert manager.read_pdf_highlights(object_id) == saved
    manager.save_pdf_highlights(object_id, PdfHighlights())
    assert manager.read_pdf_highlights(object_id).highlights == []
    assert not list(Path(paper.file_path).parent.glob("*.tmp"))
