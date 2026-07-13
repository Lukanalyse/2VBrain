from pathlib import Path
from tempfile import SpooledTemporaryFile

from pypdf import PdfWriter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.settings import Settings
from database.base import Base
from repositories.library_repository import LibraryRepository
from schemas.concept import ConceptCreate
from schemas.connections import ConnectionType
from services.concept_manager import ConceptManager
from services.connection_manager import ConnectionManager
from services.library_manager import IncomingDocument, LibraryManager
from services.linking_engine import LinkingEngine
from services.vault_manager import VaultManager


def make_pdf(filename: str) -> IncomingDocument:
    file = SpooledTemporaryFile()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_metadata({"/Title": Path(filename).stem})
    writer.write(file)
    file.seek(0)
    return IncomingDocument(filename=filename, file=file, content_type="application/pdf")


def make_manager(tmp_path: Path):
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
        ConnectionManager(db=session, linking_engine=linking_engine),
        LibraryManager(settings=settings, repository=repository, vault_manager=vault_manager),
        concept_manager,
    )


def test_connection_manager_creates_lists_deletes_and_exports_graph_data(tmp_path: Path) -> None:
    manager, library_manager, concept_manager = make_manager(tmp_path)
    paper = library_manager.import_pdf(make_pdf("Connection Paper.pdf"))
    concept = concept_manager.create_concept(ConceptCreate(name="Thompson Sampling"))

    connection = manager.create_connection(
        source_id=f"paper:{paper.id}",
        target_id=f"concept:{concept.slug}",
        relation_type=ConnectionType.uses,
    )

    assert connection.relation_type == ConnectionType.related
    assert connection.source.title == "Connection Paper"
    assert connection.target.title == "Thompson Sampling"

    listed = manager.list_connections(f"paper:{paper.id}")
    assert [item.id for item in listed.outgoing] == [connection.id]
    assert listed.incoming == []

    target_listed = manager.list_connections(f"concept:{concept.slug}")
    assert [item.id for item in target_listed.incoming] == [connection.id]

    graph = manager.graph_data()
    assert {node.id for node in graph.nodes} == {f"paper:{paper.id}", f"concept:{concept.slug}"}
    assert [(edge.source_id, edge.target_id, edge.relation_type) for edge in graph.edges] == [
        (f"paper:{paper.id}", f"concept:{concept.slug}", ConnectionType.related)
    ]

    manager.delete_connection(connection.id)
    assert manager.list_connections(f"paper:{paper.id}").outgoing == []
