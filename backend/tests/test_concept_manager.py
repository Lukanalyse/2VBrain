from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.settings import Settings
from database.base import Base
from models.library_item import LibraryItem
from repositories.library_repository import LibraryRepository
from schemas.concept import ConceptCreate
from services.concept_manager import ConceptManager
from services.vault_manager import VaultManager


def make_manager(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", future=True)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, future=True)()

    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    paper_markdown = vault / "02 Library" / "Papers" / "Paper.md"
    paper_markdown.parent.mkdir(parents=True)
    paper_markdown.write_text("# Summary\n\n# Related Concepts\n\n", encoding="utf-8")

    item = LibraryItem(
        filename="Paper.pdf",
        original_filename="Paper.pdf",
        file_path=str(tmp_path / "Paper.pdf"),
        markdown_path=str(paper_markdown),
        imported_at=datetime.now(UTC),
        status="unread",
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    settings = Settings(
        workspace_config_path=tmp_path / "workspace.json",
        library_path=tmp_path / "library",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
    )
    vault_manager = VaultManager(settings)
    vault_manager.save_vault_path(vault)

    return ConceptManager(
        vault_manager=vault_manager,
        library_repository=LibraryRepository(session),
    ), item, paper_markdown


def test_concept_manager_creates_concept_and_links_paper(tmp_path: Path) -> None:
    manager, item, paper_markdown = make_manager(tmp_path)

    concept = manager.create_concept(
        ConceptCreate(
            name="Thompson Sampling",
            description="Bayesian bandit algorithm",
            category="Algorithm",
            tags=["bandits", "bayesian"],
        )
    )

    assert Path(concept.markdown_path).exists()
    assert "type: concept" in Path(concept.markdown_path).read_text(encoding="utf-8")

    linked = manager.link_paper_concepts(item, ["Thompson Sampling"])

    assert linked == ["Thompson Sampling"]
    assert "[[Thompson Sampling]]" in paper_markdown.read_text(encoding="utf-8")
    assert manager.get_linked_papers("Thompson Sampling")[0].id == item.id
