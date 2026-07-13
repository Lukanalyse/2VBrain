import { writable } from 'svelte/store';

import type { KnowledgeConceptView } from '$lib/features/explore/types/explore';

export const selectedExploreConcept = writable<KnowledgeConceptView | null>(
  null
);
