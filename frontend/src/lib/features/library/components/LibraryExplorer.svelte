<script lang="ts">
  import { ArrowDownAZ, ArrowUpAZ, ChevronRight, Search } from '@lucide/svelte';
  import { onMount } from 'svelte';

  import { goto } from '$app/navigation';
  import NeuralCore from '$lib/components/NeuralCore.svelte';
  import ObjectMenu from '$lib/components/ui/ObjectMenu.svelte';
  import { entityMeta, entityTypes } from '$lib/design/entities';
  import type {
    LinkableObject,
    LinkableType
  } from '$lib/features/linking/types/linking';
  import { searchExplorer } from '$lib/features/research-explorer/services/researchExplorerApi';

  let objects = $state<LinkableObject[]>([]);
  let loading = $state(true);
  let query = $state('');
  let ascending = $state(true);
  let collapsed = $state<Record<string, boolean>>({});

  export async function load(): Promise<void> {
    loading = true;
    try {
      objects = await searchExplorer('', entityTypes);
    } catch {
      objects = [];
    } finally {
      loading = false;
    }
  }

  onMount(load);

  let normalizedQuery = $derived(query.trim().toLowerCase());

  let filtered = $derived(
    normalizedQuery
      ? objects.filter((object) =>
          [object.title, object.subtitle]
            .filter(Boolean)
            .some((value) => value.toLowerCase().includes(normalizedQuery))
        )
      : objects
  );

  let groups = $derived(
    entityTypes
      .map((type) => ({
        type,
        meta: entityMeta[type],
        items: filtered
          .filter((object) => object.type === type)
          .sort((a, b) =>
            ascending
              ? a.title.localeCompare(b.title)
              : b.title.localeCompare(a.title)
          )
      }))
      .filter((group) => group.items.length > 0)
  );

  let total = $derived(filtered.length);

  function isCollapsed(type: LinkableType): boolean {
    // A search auto-expands every matching group.
    return !normalizedQuery && collapsed[type] === true;
  }

  function toggle(type: LinkableType): void {
    collapsed = { ...collapsed, [type]: !collapsed[type] };
  }

  function open(object: LinkableObject): void {
    void goto(`/workspace?open=${encodeURIComponent(object.id)}`);
  }

  function handleDeleted(objectId: string): void {
    objects = objects.filter((object) => object.id !== objectId);
  }
</script>

<div class="library-index flex min-h-0 flex-col">
  <div
    class="index-toolbar flex flex-wrap items-center gap-2 border-b border-border py-3 md:flex-nowrap"
  >
    <label class="ros-input-affix min-w-0 flex-1">
      <Search size={15} />
      <input
        bind:value={query}
        class="min-w-0 flex-1 bg-transparent text-foreground outline-none placeholder:text-muted-foreground"
        placeholder="Search the complete index..."
      />
    </label>
    <button
      class="ros-btn-icon h-9 w-9 shrink-0"
      type="button"
      aria-label={ascending ? 'Sort Z to A' : 'Sort A to Z'}
      title={ascending ? 'Sort Z to A' : 'Sort A to Z'}
      onclick={() => (ascending = !ascending)}
    >
      {#if ascending}
        <ArrowDownAZ size={15} />
      {:else}
        <ArrowUpAZ size={15} />
      {/if}
    </button>
    <span class="index-count shrink-0 text-xs text-muted-foreground">
      <span class="h-1.5 w-1.5 bg-accent"></span>
      {total} objects
    </span>
  </div>

  {#if loading}
    <div class="mt-4 grid gap-2">
      {#each Array(6) as _}
        <div class="h-8 rounded-md border border-border bg-muted/15"></div>
      {/each}
    </div>
  {:else if !groups.length}
    <div class="index-empty mt-3 flex flex-col items-center justify-center px-6 py-10 text-center">
      <NeuralCore
        compact
        label="Memory Bank"
        detail={query ? 'No matching signal' : 'Awaiting first source'}
      />
      <h3 class="text-base font-semibold text-foreground">
        {query ? 'No object matches your search.' : 'Your Library is empty.'}
      </h3>
      <p class="mt-2 max-w-sm text-sm text-muted-foreground">
        {query
          ? 'Try a different term.'
          : 'Import a PDF or create a concept, project, or note to get started.'}
      </p>
    </div>
  {:else}
    <div class="mt-3 grid gap-3 overflow-y-auto pb-8">
      {#each groups as group (group.type)}
        {@const Icon = group.meta.icon}
        <section class="index-group">
          <button
            class="index-group-header flex w-full items-center gap-2 px-2 py-2 text-left transition hover:bg-muted/20"
            type="button"
            onclick={() => toggle(group.type)}
          >
            <ChevronRight
              size={14}
              class={`shrink-0 text-muted-foreground transition-transform ${isCollapsed(group.type) ? '' : 'rotate-90'}`}
            />
            <Icon size={15} class={`shrink-0 ${group.meta.text}`} />
            <span class={`text-sm font-semibold ${group.meta.text}`}>
              {group.meta.plural}
            </span>
            <span class="ml-auto text-xs text-muted-foreground">{group.items.length}</span>
          </button>

          {#if !isCollapsed(group.type)}
            <div class="index-items grid">
              {#each group.items as object (object.id)}
                <div
                  class={`index-row group flex items-center gap-2 border-l-2 ${group.meta.borderLeft} pl-3 pr-1 transition hover:bg-muted/20`}
                >
                  <button
                    class="flex min-w-0 flex-1 items-center gap-2 py-2 text-left"
                    type="button"
                    onclick={() => open(object)}
                  >
                    <Icon size={14} class={`shrink-0 ${group.meta.text}`} />
                    <span class="min-w-0 flex-1">
                      <span class="block truncate text-sm text-foreground"
                        >{object.title}</span
                      >
                      {#if object.subtitle}
                        <span
                          class="block truncate text-xs leading-tight text-muted-foreground"
                          >{object.subtitle}</span
                        >
                      {/if}
                    </span>
                  </button>
                  <div class="opacity-0 transition group-hover:opacity-100">
                    <ObjectMenu
                      objectId={object.id}
                      title={object.title}
                      onDeleted={handleDeleted}
                      onRenamed={load}
                      onDuplicated={load}
                      onMoved={load}
                    />
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </section>
      {/each}
    </div>
  {/if}
</div>

<style>
  .index-toolbar {
    position: relative;
  }

  .index-toolbar::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    width: 72px;
    height: 1px;
    background: hsl(var(--accent) / 0.7);
  }

  .index-count {
    display: inline-flex;
    height: 34px;
    align-items: center;
    gap: 7px;
    border-left: 1px solid hsl(var(--border));
    padding-left: 10px;
  }

  .index-empty {
    min-height: 500px;
    border-block: 1px solid hsl(var(--border));
    background: hsl(var(--background) / 0.48);
  }

  .index-empty h3 {
    margin-top: -12px;
  }

  .index-group {
    position: relative;
    border-block: 1px solid hsl(var(--border));
    background: hsl(var(--background) / 0.58);
  }

  .index-group::before {
    content: '';
    position: absolute;
    left: -12px;
    top: 18px;
    width: 8px;
    height: 8px;
    border: 1px solid hsl(var(--accent) / 0.5);
    background: hsl(var(--background));
  }

  .index-group-header {
    border-bottom: 1px solid transparent;
  }

  .index-items {
    border-top: 1px solid hsl(var(--border));
  }

  .index-row + .index-row {
    border-top: 1px solid hsl(var(--border) / 0.65);
  }
</style>
