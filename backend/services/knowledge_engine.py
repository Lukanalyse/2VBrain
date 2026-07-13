from schemas.concept import ConceptResponse
from schemas.knowledge_engine import KnowledgeConceptSummary, KnowledgeConceptView
from schemas.library import LibraryItemResponse
from services.concept_manager import ConceptManager


class KnowledgeEngine:
    """Resolves Markdown-based knowledge relations. Contains no AI logic."""

    def __init__(self, concept_manager: ConceptManager) -> None:
        self._concept_manager = concept_manager

    def list_concepts(self) -> list[KnowledgeConceptSummary]:
        summaries = []
        for concept in self._concept_manager.list_concepts():
            content = self._concept_manager.get_concept_content(concept.slug)
            summaries.append(
                KnowledgeConceptSummary(
                    concept=concept,
                    description=self._description(content),
                    related_papers_count=len(self._concept_manager.get_linked_papers(concept.name)),
                    related_concepts_count=len(
                        self._concept_manager.extract_section_links(content, "Related Concepts")
                    ),
                    related_projects_count=len(
                        self._concept_manager.extract_section_links(content, "Related Projects")
                    ),
                )
            )
        return summaries

    def get_concept_view(self, slug: str) -> KnowledgeConceptView:
        concept, content, linked_papers = self._concept_manager.get_concept_detail(slug)
        concept_lookup = {item.name: item for item in self._concept_manager.list_concepts()}
        related_concepts = [
            concept_lookup[name]
            for name in self._concept_manager.extract_section_links(content, "Related Concepts")
            if name in concept_lookup
        ]

        return KnowledgeConceptView(
            concept=concept,
            description=self._description(content),
            related_papers=[LibraryItemResponse.model_validate(item) for item in linked_papers],
            related_concepts=related_concepts,
            related_projects=self._concept_manager.extract_section_links(content, "Related Projects"),
            brainstorm_notes=self._concept_manager.extract_section_links(content, "Brainstorm"),
        )

    def link_related_concepts(self, slug: str, concept_names: list[str]) -> list[str]:
        return self._concept_manager.link_related_concepts(slug, concept_names)

    def _description(self, content: str) -> str:
        section = self._concept_manager.extract_section_text(content, "Description").strip()
        return section.splitlines()[0].strip() if section else ""
