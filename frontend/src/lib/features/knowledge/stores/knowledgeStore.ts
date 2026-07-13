import { writable } from 'svelte/store';

import type { KnowledgeItem } from '$lib/features/knowledge/types/knowledge';

export const activeKnowledgeItem = writable<KnowledgeItem | null>(null);
