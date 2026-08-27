<script lang="ts">
  import {
    ArrowLeft,
    ArrowRight,
    Boxes,
    Brain,
    FileText,
    Lightbulb,
    Search,
    StickyNote,
    BookOpenText
  } from '@lucide/svelte';
  import { onDestroy, onMount } from 'svelte';

  import Card from '$lib/components/ui/Card.svelte';
  import PageHeader from '$lib/components/ui/PageHeader.svelte';
  import type {
    LinkableObject,
    LinkableType
  } from '$lib/features/linking/types/linking';
  import {
    getExplorerDetail,
    searchExplorer
  } from '$lib/features/research-explorer/services/researchExplorerApi';
  import type { ExplorerObjectDetail } from '$lib/features/research-explorer/types/researchExplorer';

  let query = '';
  let results: LinkableObject[] = [];
  let selected: ExplorerObjectDetail | null = null;
  let recentlyVisited: LinkableObject[] = [];
  let history: LinkableObject[] = [];
  let historyIndex = -1;
  let isLoading = true;
  let isSearching = false;
  let errorMessage: string | null = null;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let hasMounted = false;
  let searchController: AbortController | null = null;
  let detailController: AbortController | null = null;
  let visibleLimit = 120;

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
  $: visibleResults = results.slice(0, visibleLimit);
  $: grouped = types.map((type) => ({
    type,
    items: visibleResults.filter((item) => item.type === type)
  }));
  $: hiddenResultCount = Math.max(0, results.length - visibleResults.length);

  onMount(async () => {
    hasMounted = true;
    try {
      results = await searchExplorer('');
      if (results[0]) await selectObject(results[0], true);
    } catch (error) {
      errorMessage =
        error instanceof Error ? error.message : 'Unable to load the index.';
    } finally {
      isLoading = false;
    }
  });

  function scheduleSearch(_query: string): void {
    if (timer) clearTimeout(timer);
    visibleLimit = 120;
    timer = setTimeout(() => void loadResults(_query), 170);
  }

  async function loadResults(value = query): Promise<void> {
    searchController?.abort();
    const controller = new AbortController();
    searchController = controller;
    isSearching = true;
    try {
      results = await searchExplorer(value, types, controller.signal);
    } catch (error) {
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        errorMessage =
          error instanceof Error ? error.message : 'Unable to search the index.';
      }
    } finally {
      if (searchController === controller) isSearching = false;
    }
  }

  async function selectObject(
    item: LinkableObject,
    pushHistory = true
  ): Promise<void> {
    errorMessage = null;
    detailController?.abort();
    const controller = new AbortController();
    detailController = controller;
    try {
      selected = await getExplorerDetail(item.id, controller.signal);
      addRecentlyVisited(selected.object);
      if (pushHistory) pushHistoryItem(selected.object);
    } catch (error) {
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        errorMessage =
          error instanceof Error ? error.message : 'Unable to open object.';
      }
    }
  }

  onDestroy(() => {
    if (timer) clearTimeout(timer);
    searchController?.abort();
    detailController?.abort();
  });

  function pushHistoryItem(item: LinkableObject): void {
    if (history[historyIndex]?.id === item.id) return;
    history = [...history.slice(0, historyIndex + 1), item];
    historyIndex = history.length - 1;
  }

  function addRecentlyVisited(item: LinkableObject): void {
    recentlyVisited = [
      item,
      ...recentlyVisited.filter((entry) => entry.id !== item.id)
    ].slice(0, 8);
  }

  async function goBack(): Promise<void> {
    if (historyIndex <= 0) return;
    historyIndex -= 1;
    await selectObject(history[historyIndex], false);
  }

  async function goForward(): Promise<void> {
    if (historyIndex >= history.length - 1) return;
    historyIndex += 1;
    await selectObject(history[historyIndex], false);
  }
</script>

<section
  class="grid min-h-[calc(100vh-4rem)] grid-cols-1 lg:grid-cols-[360px_minmax(0,1fr)_320px]"
>
  <aside
    class="border-b border-border bg-background/55 p-4 lg:border-b-0 lg:border-r"
  >
    <PageHeader
      eyebrow="Research Explorer"
      title="Explore"
      description="Search and navigate connected research objects."
      compact
    />

    <label
      class="mt-5 flex h-11 items-center gap-2 rounded-md border border-border bg-muted/25 px-3 text-sm text-muted-foreground focus-within:border-accent/45"
    >
      <Search size={16} />
      <input
        bind:value={query}
        class="min-w-0 flex-1 bg-transparent text-foreground outline-none placeholder:text-muted-foreground"
        placeholder="Search everything"
        type="search"
      />
    </label>

    <div class="mt-4 flex gap-2">
      <button
        class="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-muted/25 px-3 text-sm text-muted-foreground transition hover:text-foreground disabled:opacity-40"
        type="button"
        disabled={historyIndex <= 0}
        on:click={goBack}
      >
        <ArrowLeft size={15} />
        Back
      </button>
      <button
        class="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-muted/25 px-3 text-sm text-muted-foreground transition hover:text-foreground disabled:opacity-40"
        type="button"
        disabled={historyIndex >= history.length - 1}
        on:click={goForward}
      >
        Forward
        <ArrowRight size={15} />
      </button>
    </div>

    <div class="mt-5 space-y-5">
      {#if isLoading}
        <p class="text-sm text-muted-foreground">Loading index…</p>
      {:else}
        {#if isSearching}
          <p class="mb-3 text-xs text-accent" aria-live="polite">Updating results…</p>
        {/if}
        {#each grouped as group}
          {#if group.items.length > 0}
            <section>
              <h2
                class="mb-2 text-xs font-medium uppercase text-muted-foreground"
              >
                {labels[group.type]}
              </h2>
              <div class="space-y-1">
                {#each group.items as item}
                  <button
                    class={[
                      'flex w-full items-center gap-3 rounded-md px-3 py-2 text-left transition',
                      selected?.object.id === item.id
                        ? 'bg-accent/10 text-foreground'
                        : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                    ]}
                    type="button"
                    on:click={() => selectObject(item)}
                  >
                    <svelte:component
                      this={icons[item.type]}
                      size={15}
                      class="text-accent"
                    />
                    <span class="min-w-0">
                      <span class="block truncate text-sm font-medium"
                        >{item.title}</span
                      >
                      <span class="mt-0.5 block truncate text-xs"
                        >{item.subtitle}</span
                      >
                    </span>
                  </button>
                {/each}
              </div>
            </section>
          {/if}
        {/each}
        {#if results.length === 0}
          <p class="text-sm text-muted-foreground">No results.</p>
        {/if}
        {#if hiddenResultCount > 0}
          <button
            class="mt-3 h-9 w-full rounded-md border border-border bg-muted/20 text-xs text-muted-foreground transition hover:text-foreground"
            type="button"
            on:click={() => (visibleLimit += 120)}
          >
            Show {Math.min(120, hiddenResultCount)} more · {hiddenResultCount} remaining
          </button>
        {/if}
      {/if}
    </div>
  </aside>

  <main class="min-w-0 border-b border-border p-5 lg:border-b-0 lg:border-r">
    {#if errorMessage}
      <Card className="p-5">
        <p class="text-sm text-muted-foreground">{errorMessage}</p>
      </Card>
    {:else if selected}
      <div class="border-b border-border pb-5">
        <p class="text-xs font-medium uppercase text-accent">
          {selected.object.type}
        </p>
        <h2 class="mt-2 text-3xl font-semibold text-foreground">
          {selected.object.title}
        </h2>
        <p class="mt-3 text-sm leading-6 text-muted-foreground">
          {selected.description || 'No description available.'}
        </p>
      </div>

      <div class="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <Card className="p-4">
          <p class="text-xs text-muted-foreground">Type</p>
          <p class="mt-2 text-sm font-medium capitalize text-foreground">
            {selected.object.type}
          </p>
        </Card>
        <Card className="p-4">
          <p class="text-xs text-muted-foreground">Parent</p>
          <p class="mt-2 truncate text-sm font-medium text-foreground">
            {selected.parent || 'Vault'}
          </p>
        </Card>
        <Card className="p-4">
          <p class="text-xs text-muted-foreground">Tags</p>
          <p class="mt-2 truncate text-sm font-medium text-foreground">
            {selected.tags.length ? selected.tags.join(', ') : 'None'}
          </p>
        </Card>
        <Card className="p-4">
          <p class="text-xs text-muted-foreground">Related</p>
          <p class="mt-2 text-sm font-medium text-foreground">
            {selected.all_related.length}
          </p>
        </Card>
      </div>

      <section class="mt-6">
        <h3 class="text-base font-semibold text-foreground">Related</h3>
        <div class="mt-4 grid gap-3 md:grid-cols-2">
          {#each selected.all_related as item}
            <button
              class="flex items-center gap-3 rounded-md border border-border bg-muted/20 px-3 py-3 text-left transition hover:border-accent/40"
              type="button"
              on:click={() => selectObject(item)}
            >
              <svelte:component
                this={icons[item.type]}
                size={16}
                class="text-accent"
              />
              <span class="min-w-0">
                <span class="block truncate text-sm font-medium text-foreground"
                  >{item.title}</span
                >
                <span class="mt-1 block text-xs uppercase text-muted-foreground"
                  >{item.type}</span
                >
              </span>
            </button>
          {:else}
            <p class="text-sm text-muted-foreground">No relations yet.</p>
          {/each}
        </div>
      </section>
    {:else}
      <p class="text-sm text-muted-foreground">Select an object to explore.</p>
    {/if}
  </main>

  <aside class="bg-background/45 p-5">
    <h2 class="text-base font-semibold text-foreground">Recently Visited</h2>
    <div class="mt-4 space-y-2">
      {#each recentlyVisited as item}
        <button
          class="block w-full rounded-md border border-border bg-muted/20 px-3 py-2 text-left text-sm text-foreground transition hover:border-accent/40"
          type="button"
          on:click={() => selectObject(item)}
        >
          <span class="block truncate">{item.title}</span>
          <span class="mt-1 block text-xs uppercase text-muted-foreground"
            >{item.type}</span
          >
        </button>
      {:else}
        <p class="text-sm text-muted-foreground">No visits yet.</p>
      {/each}
    </div>

    {#if selected}
      <div class="mt-6 border-t border-border pt-5">
        <h2 class="text-base font-semibold text-foreground">Relation Groups</h2>
        <div class="mt-4 space-y-4">
          {#each types as type}
            <section>
              <h3 class="text-xs font-medium uppercase text-muted-foreground">
                Related {labels[type]}
              </h3>
              <div class="mt-2 space-y-1">
                {#each selected.related[type] as item}
                  <button
                    class="block w-full rounded-md px-2 py-1.5 text-left text-sm text-muted-foreground hover:bg-muted/40 hover:text-foreground"
                    type="button"
                    on:click={() => selectObject(item)}
                  >
                    {item.title}
                  </button>
                {:else}
                  <p class="px-2 py-1.5 text-xs text-muted-foreground">Empty</p>
                {/each}
              </div>
            </section>
          {/each}
        </div>
      </div>
    {/if}
  </aside>
</section>
