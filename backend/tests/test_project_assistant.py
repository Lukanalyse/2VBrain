from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.settings import Settings
from database.base import Base
from repositories.assistant_repository import AssistantRepository
from repositories.library_repository import LibraryRepository
from schemas.assistant import GroundedAnswerPayload, ProjectAssistantQuery
from services.assistant_config_manager import (
    AssistantConfigError,
    AssistantConfigManager,
)
from services.concept_manager import ConceptManager
from services.hybrid_retriever import HybridRetriever
from services.linking_engine import LinkingEngine
from services.ollama_client import OllamaClient
from services.project_assistant import ProjectAssistant
from services.project_corpus import ProjectCorpusResolver
from services.project_indexer import ProjectIndexer
from services.vault_manager import VaultManager


class FakeOllama:
    def __init__(self, citation: str = "S1") -> None:
        self.citation = citation
        self.answer_calls = 0

    def embed(self, texts: list[str], model: str) -> list[list[float]]:
        del model
        return [self._embedding(text) for text in texts]

    def grounded_answer(self, **_: object) -> GroundedAnswerPayload:
        self.answer_calls += 1
        return GroundedAnswerPayload(
            answer=f"The project evidence supports this answer [{self.citation}].",
            primary_citation=self.citation,
            citations=[self.citation],
            insufficient_evidence=False,
        )

    def _embedding(self, text: str) -> list[float]:
        normalized = text.lower()
        if "alpha" in normalized or "42 percent" in normalized:
            return [1.0, 0.0]
        if "beta" in normalized or "99 percent" in normalized:
            return [0.0, 1.0]
        return [0.0, 0.0]


class CapturingOllama(OllamaClient):
    def __init__(self) -> None:
        super().__init__("http://127.0.0.1:11434")
        self.payload: dict[str, object] | None = None

    def _request(
        self,
        path: str,
        payload: dict[str, object] | None = None,
        *,
        timeout: int,
    ) -> dict[str, object]:
        del path, timeout
        self.payload = payload
        return {
            "message": {
                "content": (
                    '{"answer":"Supported [S2].","primary_citation":"S2",'
                    '"citations":["S2"],"insufficient_evidence":false}'
                )
            }
        }


def make_assistant(tmp_path: Path, citation: str = "S1"):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", future=True)
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine, future=True)()

    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    projects = vault / "01 Projects"
    brainstorms = vault / "04 Brainstorm"
    projects.mkdir()
    brainstorms.mkdir()
    (projects / "Alpha.md").write_text(
        "# Overview\n\nAlpha project.\n\n# Brainstorm\n\n- [[Alpha Idea]]\n",
        encoding="utf-8",
    )
    (projects / "Beta.md").write_text(
        "# Overview\n\nBeta project.\n\n# Brainstorm\n\n- [[Beta Idea]]\n",
        encoding="utf-8",
    )
    alpha_path = brainstorms / "Alpha Idea.md"
    alpha_path.write_text(
        "# Findings\n\nAlpha evidence reports an increase of 42 percent.\n\n"
        "# Related Ideas\n\n- [[Beta Idea]]\n",
        encoding="utf-8",
    )
    (brainstorms / "Beta Idea.md").write_text(
        "# Findings\n\nBeta private evidence reports 99 percent.\n",
        encoding="utf-8",
    )

    settings = Settings(
        workspace_config_path=tmp_path / "workspace.json",
        assistant_config_path=tmp_path / "assistant.json",
        library_path=tmp_path / "library",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
    )
    vault_manager = VaultManager(settings)
    vault_manager.save_vault_path(vault)
    library_repository = LibraryRepository(db)
    concept_manager = ConceptManager(
        vault_manager=vault_manager,
        library_repository=library_repository,
    )
    linking_engine = LinkingEngine(
        vault_manager=vault_manager,
        library_repository=library_repository,
        concept_manager=concept_manager,
    )
    repository = AssistantRepository(db)
    fake_ollama = FakeOllama(citation)
    resolver = ProjectCorpusResolver(
        vault_manager=vault_manager,
        library_repository=library_repository,
        linking_engine=linking_engine,
    )
    indexer = ProjectIndexer(
        corpus_resolver=resolver,
        repository=repository,
        ollama=fake_ollama,
    )
    config_manager = AssistantConfigManager(settings)
    assistant = ProjectAssistant(
        config_manager=config_manager,
        ollama=fake_ollama,
        indexer=indexer,
        retriever=HybridRetriever(repository),
    )
    return assistant, repository, indexer, config_manager, fake_ollama, alpha_path


def test_project_index_never_includes_transitive_project_sources(tmp_path: Path) -> None:
    _, repository, indexer, config_manager, _, _ = make_assistant(tmp_path)

    status = indexer.index("project:Alpha", config_manager.read())
    contents = "\n".join(record.content for record in repository.project_chunks("project:Alpha"))

    assert status.ready is True
    assert "42 percent" in contents
    assert "99 percent" not in contents
    assert "Beta private evidence" not in contents


def test_project_index_rejects_symlinks_outside_managed_roots(tmp_path: Path) -> None:
    _, repository, indexer, config_manager, _, alpha_path = make_assistant(tmp_path)
    outside = tmp_path / "outside-secret.md"
    outside.write_text("This private material is outside the project vault.", encoding="utf-8")
    notes_dir = alpha_path.parent / f"{alpha_path.stem}.notes"
    notes_dir.mkdir()
    (notes_dir / "Escaped.md").symlink_to(outside)

    status = indexer.index("project:Alpha", config_manager.read())
    contents = "\n".join(record.content for record in repository.project_chunks("project:Alpha"))

    assert status.ready is True
    assert "outside the project vault" not in contents


def test_changed_project_note_is_reindexed(tmp_path: Path) -> None:
    _, repository, indexer, config_manager, _, alpha_path = make_assistant(tmp_path)
    config = config_manager.read()
    first = indexer.index("project:Alpha", config)
    second = indexer.index("project:Alpha", config)

    alpha_path.write_text(
        "# Findings\n\nAlpha evidence was revised to 43 percent.\n",
        encoding="utf-8",
    )
    third = indexer.index("project:Alpha", config)
    contents = "\n".join(record.content for record in repository.project_chunks("project:Alpha"))

    assert first.updated_documents > 0
    assert second.updated_documents == 0
    assert third.updated_documents == 1
    assert "43 percent" in contents
    assert "42 percent" not in contents


def test_unchanged_sources_are_not_reextracted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, indexer, config_manager, _, _ = make_assistant(tmp_path)
    config = config_manager.read()
    indexer.index("project:Alpha", config)

    def fail_if_extracted(*_: object) -> None:
        raise AssertionError("unchanged sources should not be extracted again")

    monkeypatch.setattr(indexer, "_extract", fail_if_extracted)

    second = indexer.index("project:Alpha", config)

    assert second.ready is True
    assert second.updated_documents == 0


def test_assistant_accepts_only_known_inline_citations(tmp_path: Path) -> None:
    assistant, _, _, _, fake_ollama, _ = make_assistant(tmp_path)

    response = assistant.answer(
        "project:Alpha",
        ProjectAssistantQuery(question="What does the Alpha evidence report?"),
    )

    assert response.insufficient_evidence is False
    assert [citation.label for citation in response.citations] == ["S1"]
    assert all(citation.object.id != "brainstorm:Beta Idea" for citation in response.citations)
    assert fake_ollama.answer_calls == 1


def test_assistant_normalizes_known_declared_citations(tmp_path: Path) -> None:
    assistant, _, _, _, fake_ollama, _ = make_assistant(tmp_path)

    def answer_without_inline_label(**_: object) -> GroundedAnswerPayload:
        return GroundedAnswerPayload(
            answer="The project evidence supports this answer.",
            primary_citation="S1",
            citations=["S1"],
            insufficient_evidence=False,
        )

    fake_ollama.grounded_answer = answer_without_inline_label  # type: ignore[method-assign]

    response = assistant.answer(
        "project:Alpha",
        ProjectAssistantQuery(question="What does the Alpha evidence report?"),
    )

    assert response.insufficient_evidence is False
    assert response.answer.endswith("[S1]")
    assert [citation.label for citation in response.citations] == ["S1"]


def test_assistant_rejects_invented_citation(tmp_path: Path) -> None:
    assistant, _, _, _, _, _ = make_assistant(tmp_path, citation="S999")

    response = assistant.answer(
        "project:Alpha",
        ProjectAssistantQuery(question="What does the Alpha evidence report?"),
    )

    assert response.insufficient_evidence is True
    assert response.citations == []


def test_assistant_refuses_before_generation_when_no_evidence_matches(tmp_path: Path) -> None:
    assistant, _, _, _, fake_ollama, _ = make_assistant(tmp_path)

    response = assistant.answer(
        "project:Alpha",
        ProjectAssistantQuery(question="Unrelated zephyr question"),
    )

    assert response.insufficient_evidence is True
    assert fake_ollama.answer_calls == 0


def test_cloud_models_are_rejected(tmp_path: Path) -> None:
    _, _, _, _, _, _ = make_assistant(tmp_path)
    settings = Settings(assistant_config_path=tmp_path / "cloud-assistant.json")
    settings.assistant_config_path.write_text(
        '{"chat_model":"qwen3:14b-cloud","embedding_model":"embeddinggemma"}',
        encoding="utf-8",
    )

    with pytest.raises(AssistantConfigError, match="Cloud-hosted"):
        AssistantConfigManager(settings).read()


def test_ollama_schema_constrains_citations_to_retrieved_labels() -> None:
    ollama = CapturingOllama()

    response = ollama.grounded_answer(
        model="qwen3:14b",
        context_length=8192,
        messages=[{"role": "user", "content": "Question"}],
        allowed_citations=["S1", "S2"],
    )

    assert response.citations == ["S2"]
    assert response.primary_citation == "S2"
    assert ollama.payload is not None
    schema = ollama.payload["format"]
    assert isinstance(schema, dict)
    properties = schema["properties"]
    assert isinstance(properties, dict)
    primary_schema = properties["primary_citation"]
    assert isinstance(primary_schema, dict)
    assert primary_schema["enum"] == ["S1", "S2", "NONE"]
    citation_schema = properties["citations"]
    assert isinstance(citation_schema, dict)
    items = citation_schema["items"]
    assert isinstance(items, dict)
    assert items["enum"] == ["S1", "S2"]
