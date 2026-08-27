<script lang="ts">
  import {
    BookOpenText,
    FileText,
    Lightbulb,
    Search,
    StickyNote,
    Boxes,
    Brain
  } from '@lucide/svelte';
  import { onDestroy, onMount } from 'svelte';

  import { searchLinkableObjects } from '$lib/features/linking/services/linkingApi';
  import type {
    LinkableObject,
    LinkableType
  } from '$lib/features/linking/types/linking';

  export let compact = false;

  let query = '';
  let results: LinkableObject[] = [];
  let isSearching = false;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let searchController: AbortController | null = null;
  let input: HTMLInputElement;
  let hasMounted = false;

  const types: LinkableType[] = [
    'paper',
    'concept',
    'project',
    'brainstorm',
    'review',
    'note'
  ];
  const labels: Record<LinkableType, string> = {
    paper: 'Papers',
    concept: 'Concepts',
    project: 'Projects',
    brainstorm: 'Brainstorm',
    review: 'Literature Reviews',
    note: 'Notes'
  };
  const icons = {
    paper: FileText,
    concept: Brain,
    project: Boxes,
    brainstorm: Lightbulb,
    review: BookOpenText,
    note: StickyNote
  };

  $: if (hasMounted) scheduleSearch(query);
  $: grouped = types.map((type) => ({
    type,
    items: results.filter((item) => item.type === type)
  }));

  function scheduleSearch(_query: string): void {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => void loadResults(_query), 160);
  }

  async function loadResults(value = query): Promise<void> {
    searchController?.abort();
    if (!value.trim()) {
      results = [];
      isSearching = false;
      return;
    }
    const controller = new AbortController();
    searchController = controller;
    isSearching = true;
    try {
      results = await searchLinkableObjects(value, types, controller.signal);
    } catch (error) {
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        results = [];
      }
    } finally {
      if (searchController === controller) isSearching = false;
    }
  }

  function hrefFor(item: LinkableObject): string {
    return `/workspace?open=${encodeURIComponent(item.id)}`;
  }

  onMount(() => {
    hasMounted = true;
    const focusSearch = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        input?.focus();
        input?.select();
      }
    };
    window.addEventListener('keydown', focusSearch);
    return () => window.removeEventListener('keydown', focusSearch);
  });

  onDestroy(() => {
    if (timer) clearTimeout(timer);
    searchController?.abort();
  });
</script>

<div class={compact ? 'relative w-full' : 'relative w-full max-w-3xl'}>
  <label
    class="flex h-11 items-center gap-2 rounded-md border border-border bg-muted/25 px-3 text-sm text-muted-foreground shadow-panel transition focus-within:border-accent/45"
  >
    <Search size={16} />
    <input
      bind:this={input}
      bind:value={query}
      class="min-w-0 flex-1 bg-transparent text-foreground outline-none placeholder:text-muted-foreground"
      placeholder="Search papers, concepts, projects, brainstorm, reviews"
      type="search"
    />
    {#if compact && !query}
      <kbd class="hidden rounded border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground 2xl:inline">⌘K</kbd>
    {/if}
  </label>

  {#if query.trim()}
    <div
      class="absolute left-0 right-0 top-12 z-40 max-h-[520px] overflow-auto rounded-lg border border-border bg-background p-3 shadow-panel"
    >
      {#if isSearching}
        <p class="px-2 pb-1 text-xs text-accent" aria-live="polite">Updating results…</p>
      {/if}
      {#if !isSearching || results.length > 0}
        {#each grouped as group}
          {#if group.items.length > 0}
            <section class="py-2">
              <h3
                class="px-2 text-xs font-medium uppercase text-muted-foreground"
              >
                {labels[group.type]}
              </h3>
              <div class="mt-2 space-y-1">
                {#each group.items as item}
                  <a
                    class="flex items-center gap-3 rounded-md px-2 py-2 text-sm text-foreground transition hover:bg-muted/50"
                    href={hrefFor(item)}
                    on:click={() => (query = '')}
                  >
                    <svelte:component
                      this={icons[item.type]}
                      size={15}
                      class="text-accent"
                    />
                    <span class="min-w-0">
                      <span class="block truncate font-medium"
                        >{item.title}</span
                      >
                      <span class="mt-0.5 block text-xs text-muted-foreground">
                        {item.search_excerpt || item.subtitle}
                      </span>
                    </span>
                  </a>
                {/each}
              </div>
            </section>
          {/if}
        {/each}
        {#if results.length === 0}
          <p class="px-2 py-2 text-sm text-muted-foreground">No results.</p>
        {/if}
      {/if}
    </div>
  {/if}
</div>
