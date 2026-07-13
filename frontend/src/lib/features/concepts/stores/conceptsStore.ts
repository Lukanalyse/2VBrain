import { writable } from 'svelte/store';

import type { Concept } from '$lib/features/concepts/types/concept';

export const concepts = writable<Concept[]>([]);
