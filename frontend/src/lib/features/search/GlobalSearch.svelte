<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import {
    ArrowRight,
    CornerDownLeft,
    FilePlus2,
    Search,
    X
  } from '@lucide/svelte';
  import { onDestroy, onMount, tick } from 'svelte';
  import type { Component } from 'svelte';

  import { entityMeta } from '$lib/design/entities';
  import { searchLinkableObjects } from '$lib/features/linking/services/linkingApi';
  import type {
    LinkableObject,
    LinkableType
  } from '$lib/features/linking/types/linking';
  import { navigationItems } from '$lib/layouts/navigation';

  export let compact = false;

  type PaletteGroup = 'Create' | 'Navigate' | 'Results';
  type PaletteEntry = {
    id: string;
    label: string;
    detail: string;
    keywords: string;
    group: PaletteGroup;
    href: string;
    icon: Component;
    iconClass: string;
    entityType?: LinkableType;
  };

  const types: LinkableType[] = [
    'paper',
    'concept',
    'project',
    'brainstorm',
    'review',
    'note'
  ];

  let isOpen = false;
  let query = '';
  let results: LinkableObject[] = [];
  let isSearching = false;
  let selectedIndex = 0;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let searchController: AbortController | null = null;
  let input: HTMLInputElement;
  let hasMounted = false;

  $: if (hasMounted && isOpen) scheduleSearch(query);
  $: currentUrl = $page.url;
  $: staticEntries = buildStaticEntries(currentUrl);
  $: normalizedQuery = query.trim().toLowerCase();
  $: matchingCommands = staticEntries.filter((entry) =>
    matches(entry, normalizedQuery)
  );
  $: resultEntries = results.slice(0, 14).map(toResultEntry);
  $: visibleEntries = [...matchingCommands, ...resultEntries].slice(0, 20);
  $: if (selectedIndex >= visibleEntries.length) selectedIndex = 0;

  function buildStaticEntries(url: URL): PaletteEntry[] {
    const currentObject = url.searchParams.get('open');
    const noteParams = new URLSearchParams();
    if (currentObject) noteParams.set('open', currentObject);
    noteParams.set('create', 'note');

    const createEntries: PaletteEntry[] = [
      {
        id: 'create-project',
        label: 'New project',
        detail: 'Start a structured research workspace',
        keywords: 'create add project workspace research',
        group: 'Create',
        href: '/workspace?create=project',
        icon: entityMeta.project.icon,
        iconClass: entityMeta.project.text,
        entityType: 'project'
      },
      {
        id: 'create-brainstorm',
        label: 'New brainstorm',
        detail: 'Capture and develop a research idea',
        keywords: 'create add brainstorm idea writing',
        group: 'Create',
        href: '/workspace?create=brainstorm',
        icon: entityMeta.brainstorm.icon,
        iconClass: entityMeta.brainstorm.text,
        entityType: 'brainstorm'
      },
      {
        id: 'create-concept',
        label: 'New concept',
        detail: 'Add a reusable concept to the knowledge base',
        keywords: 'create add concept knowledge definition',
        group: 'Create',
        href: '/workspace?create=concept',
        icon: entityMeta.concept.icon,
        iconClass: entityMeta.concept.text,
        entityType: 'concept'
      }
    ];

    if (currentObject) {
      createEntries.unshift({
        id: 'create-note',
        label: 'New note in current thread',
        detail: 'Attach a note to the object you are viewing',
        keywords: 'create add note current paper project thread',
        group: 'Create',
        href: `/workspace?${noteParams.toString()}`,
        icon: entityMeta.note.icon,
        iconClass: entityMeta.note.text,
        entityType: 'note'
      });
    }

    const navigateEntries: PaletteEntry[] = navigationItems.map((item) => ({
      id: `navigate-${item.label.toLowerCase()}`,
      label: `Go to ${item.label}`,
      detail: navigationDetail(item.label),
      keywords: `open navigate go ${item.label}`.toLowerCase(),
      group: 'Navigate',
      href: item.href,
      icon: item.icon,
      iconClass:
        url.pathname === item.href ? 'text-accent' : 'text-muted-foreground'
    }));

    return [...createEntries, ...navigateEntries];
  }

  function navigationDetail(label: string): string {
    const details: Record<string, string> = {
      Home: 'Return to the Research OS hub',
      Workspace: 'Open your active research desk',
      Assistant: 'Ask questions across a project',
      Library: 'Browse the complete object index',
      Map: 'Explore connections and structure',
      Settings: 'Manage storage and local AI'
    };
    return details[label] ?? 'Open this area';
  }

  function matches(entry: PaletteEntry, value: string): boolean {
    if (!value) return true;
    return `${entry.label} ${entry.detail} ${entry.keywords}`
      .toLowerCase()
      .includes(value);
  }

  function toResultEntry(item: LinkableObject): PaletteEntry {
    return {
      id: `object-${item.id}`,
      label: item.title,
      detail:
        item.search_excerpt || item.subtitle || entityMeta[item.type].label,
      keywords: `${item.title} ${item.subtitle}`,
      group: 'Results',
      href: `/workspace?open=${encodeURIComponent(item.id)}`,
      icon: entityMeta[item.type].icon,
      iconClass: entityMeta[item.type].text,
      entityType: item.type
    };
  }

  function scheduleSearch(value: string): void {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => void loadResults(value), 140);
  }

  async function loadResults(value: string): Promise<void> {
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

  async function openPalette(): Promise<void> {
    isOpen = true;
    query = '';
    results = [];
    selectedIndex = 0;
    await tick();
    input?.focus();
  }

  function closePalette(): void {
    isOpen = false;
    query = '';
    results = [];
    searchController?.abort();
    isSearching = false;
  }

  function run(entry: PaletteEntry): void {
    closePalette();
    void goto(entry.href);
  }

  function handleInputKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      event.preventDefault();
      closePalette();
      return;
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      selectedIndex = visibleEntries.length
        ? (selectedIndex + 1) % visibleEntries.length
        : 0;
      return;
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      selectedIndex = visibleEntries.length
        ? (selectedIndex - 1 + visibleEntries.length) % visibleEntries.length
        : 0;
      return;
    }
    if (event.key === 'Enter' && visibleEntries[selectedIndex]) {
      event.preventDefault();
      run(visibleEntries[selectedIndex]);
    }
  }

  onMount(() => {
    hasMounted = true;
    const handleGlobalShortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        if (isOpen) closePalette();
        else void openPalette();
      }
    };
    window.addEventListener('keydown', handleGlobalShortcut);
    return () => window.removeEventListener('keydown', handleGlobalShortcut);
  });

  onDestroy(() => {
    if (timer) clearTimeout(timer);
    searchController?.abort();
  });
</script>

<button
  type="button"
  class={compact
    ? 'command-trigger flex h-9 w-full items-center gap-2 rounded-md border border-border/90 bg-surface-raised/70 px-2.5 text-left text-xs text-muted-foreground transition hover:border-accent/40 hover:bg-muted/60 hover:text-foreground'
    : 'command-trigger flex h-11 w-full items-center gap-2 rounded-md border border-border/90 bg-surface-raised/70 px-3 text-left text-sm text-muted-foreground transition hover:border-accent/40 hover:text-foreground'}
  aria-haspopup="dialog"
  aria-expanded={isOpen}
  aria-label="Open command palette"
  title="Search and commands (⌘ K)"
  onclick={openPalette}
>
  <Search size={15} class="shrink-0" />
  <span class="hidden min-w-0 flex-1 truncate xl:block">
    Search or run a command…
  </span>
  <kbd
    class="ml-auto hidden shrink-0 items-center gap-0.5 rounded border border-border bg-background/70 px-1.5 py-0.5 font-sans text-[10px] text-muted-foreground xl:inline-flex"
    >⌘ K</kbd
  >
</button>

{#if isOpen}
  <div
    class="command-backdrop fixed inset-0 z-50 flex items-start justify-center bg-background/78 px-3 pt-[10vh] backdrop-blur-sm sm:px-6 sm:pt-[14vh]"
    role="presentation"
    onclick={(event) => {
      if (event.target === event.currentTarget) closePalette();
    }}
  >
    <div
      class="command-dialog w-full max-w-2xl overflow-hidden rounded-xl border border-border bg-surface shadow-2xl"
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
    >
      <div class="flex items-center gap-3 border-b border-border px-4">
        <Search size={19} class="shrink-0 text-accent" />
        <input
          bind:this={input}
          bind:value={query}
          class="h-14 min-w-0 flex-1 bg-transparent text-base text-foreground outline-none placeholder:text-muted-foreground"
          placeholder="Search objects or type a command…"
          role="combobox"
          aria-expanded="true"
          aria-controls="command-results"
          aria-activedescendant={visibleEntries[selectedIndex]
            ? `palette-${visibleEntries[selectedIndex].id}`
            : undefined}
          autocomplete="off"
          onkeydown={handleInputKeydown}
        />
        {#if isSearching}
          <span
            class="command-searching h-4 w-4 rounded-full border-2 border-accent/25 border-t-accent"
            aria-label="Searching"
          ></span>
        {:else if query}
          <button
            type="button"
            class="ros-btn-icon h-7 w-7 border-0 bg-transparent"
            aria-label="Clear command search"
            onclick={() => {
              query = '';
              input?.focus();
            }}
          >
            <X size={14} />
          </button>
        {/if}
      </div>

      <div
        id="command-results"
        class="max-h-[min(62vh,540px)] overflow-y-auto p-2"
        role="listbox"
      >
        {#if visibleEntries.length}
          {#each visibleEntries as entry, index (entry.id)}
            {#if index === 0 || visibleEntries[index - 1].group !== entry.group}
              <p
                class="px-2 pb-1 pt-2 text-[0.66rem] font-semibold uppercase tracking-[0.1em] text-muted-foreground"
              >
                {entry.group}
              </p>
            {/if}
            <button
              id={`palette-${entry.id}`}
              type="button"
              class:command-option--selected={selectedIndex === index}
              class="command-option flex w-full items-center gap-3 rounded-lg border border-transparent px-2.5 py-2 text-left transition"
              style={entry.entityType
                ? `--entry-entity: ${entityMeta[entry.entityType].hslVar}`
                : undefined}
              role="option"
              aria-selected={selectedIndex === index}
              onmouseenter={() => (selectedIndex = index)}
              onclick={() => run(entry)}
            >
              <span
                class={`command-option-icon flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-border bg-background/55 ${entry.iconClass}`}
              >
                <svelte:component this={entry.icon} size={16} />
              </span>
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm font-medium text-foreground"
                  >{entry.label}</span
                >
                <span
                  class="mt-0.5 block truncate text-xs text-muted-foreground"
                  >{entry.detail}</span
                >
              </span>
              {#if selectedIndex === index}
                <span
                  class="flex shrink-0 items-center gap-1 text-[10px] text-muted-foreground"
                >
                  Open <CornerDownLeft size={12} />
                </span>
              {:else if entry.group === 'Create'}
                <FilePlus2
                  size={13}
                  class="shrink-0 text-muted-foreground/60"
                />
              {:else}
                <ArrowRight
                  size={13}
                  class="shrink-0 text-muted-foreground/60"
                />
              {/if}
            </button>
          {/each}
        {:else if normalizedQuery && !isSearching}
          <div class="flex flex-col items-center px-6 py-12 text-center">
            <span
              class="flex h-11 w-11 items-center justify-center rounded-lg border border-border bg-muted/20 text-muted-foreground"
            >
              <Search size={18} />
            </span>
            <p class="mt-3 text-sm font-medium text-foreground">
              No matching object or command
            </p>
            <p class="mt-1 text-xs text-muted-foreground">
              Try a title, concept, project, or area of the app.
            </p>
          </div>
        {/if}
      </div>

      <footer
        class="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-border bg-background/35 px-4 py-2 text-[10px] text-muted-foreground"
      >
        <span><kbd>↑</kbd><kbd>↓</kbd> Navigate</span>
        <span><kbd>↵</kbd> Open</span>
        <span><kbd>esc</kbd> Close</span>
        <span class="ml-auto hidden sm:inline"
          >Objects keep their identity colour throughout Research OS</span
        >
      </footer>
    </div>
  </div>
{/if}

<style>
  .command-trigger {
    box-shadow: inset 0 1px 0 hsl(var(--foreground) / 0.04);
  }

  .command-dialog {
    box-shadow:
      0 28px 80px hsl(210 20% 2% / 0.58),
      inset 0 1px 0 hsl(var(--foreground) / 0.06);
  }

  .command-dialog::before {
    content: '';
    display: block;
    height: 2px;
    background: linear-gradient(
      90deg,
      transparent,
      hsl(var(--accent) / 0.8),
      transparent
    );
  }

  .command-option--selected {
    border-color: hsl(var(--entry-entity, var(--accent)) / 0.4);
    background: hsl(var(--entry-entity, var(--accent)) / 0.09);
  }

  .command-option[style] .command-option-icon {
    border-color: hsl(var(--entry-entity) / 0.32);
    background: hsl(var(--entry-entity) / 0.07);
  }

  .command-searching {
    animation: command-spin 700ms linear infinite;
  }

  footer kbd {
    margin-right: 3px;
    border: 1px solid hsl(var(--border));
    border-radius: 4px;
    background: hsl(var(--surface-raised) / 0.75);
    padding: 1px 4px;
    color: hsl(var(--foreground) / 0.8);
    font-family: inherit;
  }

  @keyframes command-spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
