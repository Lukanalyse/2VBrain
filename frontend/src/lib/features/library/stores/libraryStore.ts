import { writable } from 'svelte/store';

import type { LibraryItem } from '$lib/features/library/types/library';

export const libraryItems = writable<LibraryItem[]>([]);
