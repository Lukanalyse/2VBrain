<script lang="ts">
  import { Link2, Search } from '@lucide/svelte';
  import { createEventDispatcher, onMount } from 'svelte';

  import {
    createLinks,
    searchLinkableObjects
  } from '$lib/features/linking/services/linkingApi';
  import type {
    LinkableObject,
    LinkableType
  } from '$lib/features/linking/types/linking';

  export let sourceId: string;
  export let excludeIds: string[] = [];
  export let allowedTypes: LinkableType[] = [];

  const dispatch = createEventDispatcher<{ linked: void }>();
  let query = '';
  let results: LinkableObject[] = [];
  let selected = new Set<string>();
  let isSearching = false;
  let isSaving = false;
  let message: string | null = null;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let hasMounted = false;

  $: if (hasMounted) scheduleSearch(query, allowedTypes);
  $: visibleResults = results.filter(
    (item) => item.id !== sourceId && !excludeIds.includes(item.id)
  );

  function scheduleSearch(_query: string, _allowedTypes: LinkableType[]): void {
    if (timer) clearTimeout(timer);
    timer = setTimeout(loadResults, 150);
  }

  async function loadResults(): Promise<void> {
    isSearching = true;
    try {
      results = await searchLinkableObjects(query, allowedTypes);
    } finally {
      isSearching = false;
    }
  }

  function toggle(id: string): void {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    selected = next;
  }

  async function save(): Promise<void> {
    if (selected.size === 0) return;
    isSaving = true;
    message = null;
    try {
      await createLinks(sourceId, Array.from(selected));
      selected = new Set();
      await loadResults();
      message = 'Links saved in Markdown.';
      dispatch('linked');
    } catch (error) {
      message =
        error instanceof Error ? error.message : 'Unable to save links.';
    } finally {
      isSaving = false;
    }
  }

  onMount(() => {
    hasMounted = true;
    void loadResults();
  });
</script>

<section class="rounded-lg border border-border bg-background/35 p-4">
  <div
    class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
  >
    <div>
      <h3 class="text-sm font-semibold text-foreground">Link Object</h3>
      <p class="mt-1 text-xs text-muted-foreground">
        Search any indexed knowledge object.
      </p>
    </div>
    <button
      class="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-accent px-3 text-sm font-medium text-accent-foreground transition hover:bg-accent/90 disabled:opacity-60"
      type="button"
      disabled={selected.size === 0 || isSaving}
      on:click={save}
    >
      <Link2 size={15} />
      Link
    </button>
  </div>

  <label
    class="mt-4 flex h-10 items-center gap-2 rounded-md border border-border bg-muted/25 px-3 text-sm text-muted-foreground focus-within:border-accent/45"
  >
    <Search size={15} />
    <input
      bind:value={query}
      class="min-w-0 flex-1 bg-transparent text-foreground outline-none placeholder:text-muted-foreground"
      placeholder="Search papers, concepts, projects, brainstorm notes, reviews"
    />
  </label>

  <div class="mt-4 max-h-72 space-y-2 overflow-auto">
    {#if isSearching}
      <p class="text-sm text-muted-foreground">Searching...</p>
    {:else if visibleResults.length === 0}
      <p class="text-sm text-muted-foreground">No objects found.</p>
    {:else}
      {#each visibleResults as item}
        <label
          class="flex cursor-pointer items-start gap-3 rounded-md border border-border bg-muted/20 px-3 py-3 transition hover:border-accent/40"
        >
          <input
            class="mt-1"
            type="checkbox"
            checked={selected.has(item.id)}
            on:change={() => toggle(item.id)}
          />
          <span class="min-w-0">
            <span class="block truncate text-sm font-medium text-foreground"
              >{item.title}</span
            >
            <span class="mt-1 block text-xs uppercase text-muted-foreground"
              >{item.type}</span
            >
          </span>
        </label>
      {/each}
    {/if}
  </div>

  {#if message}
    <p
      class="mt-4 rounded-md border border-border bg-muted/25 px-3 py-2 text-sm text-muted-foreground"
    >
      {message}
    </p>
  {/if}
</section>
