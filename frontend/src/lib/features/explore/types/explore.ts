import type { Concept } from '$lib/features/concepts/types/concept';
import type { LibraryItem } from '$lib/features/library/types/library';

export type KnowledgeConceptSummary = {
  concept: Concept;
  description: string;
  related_papers_count: number;
  related_concepts_count: number;
  related_projects_count: number;
};

export type KnowledgeConceptView = {
  concept: Concept;
  description: string;
  related_papers: LibraryItem[];
  related_concepts: Concept[];
  related_projects: string[];
  brainstorm_notes: string[];
};

export type ExploreListResponse = {
  concepts: KnowledgeConceptSummary[];
};

export type ConceptConceptLinksResponse = {
  concept_names: string[];
};
