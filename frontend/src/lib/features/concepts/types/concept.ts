import type { LibraryItem } from '$lib/features/library/types/library';

export type Concept = {
  name: string;
  slug: string;
  category: string;
  tags: string[];
  markdown_path: string;
  created: string | null;
  updated: string | null;
  linked_papers_count: number;
  linked_concepts_count: number;
};

export type ConceptCreate = {
  name: string;
  description: string;
  category: string;
  tags: string[];
};

export type ConceptListResponse = {
  concepts: Concept[];
};

export type ConceptDetail = {
  concept: Concept;
  content: string;
  linked_papers: LibraryItem[];
};

export type PaperConceptLinks = {
  concept_names: string[];
};
