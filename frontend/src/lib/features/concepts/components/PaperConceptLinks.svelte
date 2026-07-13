<script lang="ts">
  import { Link2 } from '@lucide/svelte';
  import { onMount } from 'svelte';

  import {
    getPaperConceptLinks,
    listConcepts,
    savePaperConceptLinks
  } from '$lib/features/concepts/services/conceptsApi';
  import type { Concept } from '$lib/features/concepts/types/concept';

  export let itemId: number;

  let concepts: Concept[] = [];
  let selected = new Set<string>();
  let message: string | null = null;
  let isLoading = true;
  let isSaving = false;

  onMount(async () => {
    try {
      const [loadedConcepts, links] = await Promise.all([
        listConcepts(),
        getPaperConceptLinks(itemId)
      ]);
      concepts = loadedConcepts;
      selected = new Set(links.concept_names);
    } finally {
      isLoading = false;
    }
  });

  function toggle(name: string): void {
    const next = new Set(selected);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    selected = next;
  }

  async function save(): Promise<void> {
    isSaving = true;
    message = null;
    try {
      const result = await savePaperConceptLinks(itemId, Array.from(selected));
      selected = new Set(result.concept_names);
      message = 'Concept links saved in the Paper Markdown note.';
    } catch (error) {
      message =
        error instanceof Error ? error.message : 'Unable to link concepts.';
    } finally {
      isSaving = false;
    }
  }
</script>

<section class="p-5">
  <div
    class="flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-end sm:justify-between"
  >
    <div>
      <p class="text-xs font-medium uppercase text-accent">Relations</p>
      <h2 class="mt-1 text-base font-semibold text-foreground">Link Concept</h2>
      <p class="mt-2 text-sm leading-6 text-muted-foreground">
        Links are written as Markdown wiki links in the Paper note, not stored
        as SQLite relations.
      </p>
    </div>
    <button
      class="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-accent px-4 text-sm font-medium text-accent-foreground transition hover:bg-accent/90 disabled:opacity-60"
      type="button"
      disabled={isSaving || isLoading}
      on:click={save}
    >
      <Link2 size={16} />
      Save Links
    </button>
  </div>

  {#if isLoading}
    <p class="mt-5 text-sm text-muted-foreground">Loading concepts...</p>
  {:else if concepts.length === 0}
    <div
      class="mt-6 rounded-lg border border-dashed border-border bg-background/35 px-6 py-10 text-center"
    >
      <h3 class="text-base font-semibold text-foreground">
        No concepts available.
      </h3>
      <p class="mt-2 text-sm text-muted-foreground">
        Create a concept from the Knowledge page first.
      </p>
      <a
        class="mt-5 inline-flex h-10 items-center justify-center rounded-md bg-accent px-4 text-sm font-medium text-accent-foreground"
        href="/"
      >
        New Concept
      </a>
    </div>
  {:else}
    {#if selected.size > 0}
      <div class="mt-5 rounded-lg border border-border bg-background/35 p-4">
        <h3 class="text-sm font-medium text-foreground">Linked Concepts</h3>
        <div class="mt-3 flex flex-wrap gap-2">
          {#each Array.from(selected) as name}
            <a
              class="rounded-md border border-border bg-muted/30 px-2.5 py-1 text-sm text-foreground transition hover:border-accent/40"
              href={`/workspace?open=${encodeURIComponent(`concept:${name}`)}`}
            >
              {name}
            </a>
          {/each}
        </div>
      </div>
    {/if}

    <div class="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {#each concepts as concept}
        <label
          class="flex cursor-pointer items-start gap-3 rounded-md border border-border bg-muted/20 px-3 py-3 transition hover:border-accent/40"
        >
          <input
            class="mt-1"
            type="checkbox"
            checked={selected.has(concept.name)}
            on:change={() => toggle(concept.name)}
          />
          <span class="min-w-0">
            <span class="block truncate text-sm font-medium text-foreground"
              >{concept.name}</span
            >
            <span class="mt-1 block text-xs text-muted-foreground">
              {concept.category || 'Uncategorized'}
            </span>
          </span>
        </label>
      {/each}
    </div>
  {/if}

  {#if message}
    <p
      class="mt-5 rounded-md border border-border bg-muted/25 px-3 py-3 text-sm text-muted-foreground"
    >
      {message}
    </p>
  {/if}
</section>
