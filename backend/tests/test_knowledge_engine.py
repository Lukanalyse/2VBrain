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
from services.knowledge_engine import KnowledgeEngine
from services.vault_manager import VaultManager


def make_engine(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", future=True)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, future=True)()

    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    paper_markdown = vault / "02 Library" / "Papers" / "Bandit Paper.md"
    paper_markdown.parent.mkdir(parents=True)
    paper_markdown.write_text("# Summary\n\n# Related Concepts\n\n", encoding="utf-8")

    item = LibraryItem(
        filename="Bandit Paper.pdf",
        original_filename="Bandit Paper.pdf",
        file_path=str(tmp_path / "Bandit Paper.pdf"),
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
    repository = LibraryRepository(session)
    concept_manager = ConceptManager(vault_manager=vault_manager, library_repository=repository)
    return KnowledgeEngine(concept_manager), concept_manager, item


def test_knowledge_engine_resolves_concept_relations(tmp_path: Path) -> None:
    engine, concept_manager, item = make_engine(tmp_path)
    for name in ["Machine Learning", "Reinforcement Learning", "Multi Armed Bandits"]:
        concept_manager.create_concept(
            ConceptCreate(name=name, description=f"{name} description", category="Theory")
        )

    concept_manager.link_related_concepts("Machine Learning", ["Reinforcement Learning"])
    concept_manager.link_related_concepts("Reinforcement Learning", ["Multi Armed Bandits"])
    concept_manager.link_paper_concepts(item, ["Multi Armed Bandits"])

    machine_learning = engine.get_concept_view("Machine Learning")
    reinforcement_learning = engine.get_concept_view("Reinforcement Learning")
    bandits = engine.get_concept_view("Multi Armed Bandits")

    assert machine_learning.related_concepts[0].name == "Reinforcement Learning"
    assert reinforcement_learning.related_concepts[0].name == "Multi Armed Bandits"
    assert bandits.related_papers[0].filename == "Bandit Paper.pdf"
