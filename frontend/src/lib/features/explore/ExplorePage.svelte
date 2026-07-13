<script lang="ts">
  import { Link2, Search } from '@lucide/svelte';
  import { onMount } from 'svelte';

  import Card from '$lib/components/ui/Card.svelte';
  import {
    getExploreConcept,
    listExploreConcepts,
    saveRelatedConcepts
  } from '$lib/features/explore/services/exploreApi';
  import { selectedExploreConcept } from '$lib/features/explore/stores/exploreStore';
  import type {
    KnowledgeConceptSummary,
    KnowledgeConceptView
  } from '$lib/features/explore/types/explore';

  let concepts: KnowledgeConceptSummary[] = [];
  let selected: KnowledgeConceptView | null = null;
  let query = '';
  let category = 'All';
  let tag = 'All';
  let selectedRelated = new Set<string>();
  let message: string | null = null;
  let isLoading = true;
  let isSaving = false;

  $: categories = [
    'All',
    ...Array.from(
      new Set(concepts.map((item) => item.concept.category).filter(Boolean))
    )
  ];
  $: tags = [
    'All',
    ...Array.from(
      new Set(concepts.flatMap((item) => item.concept.tags).filter(Boolean))
    )
  ];
  $: filtered = concepts.filter((item) => {
    const matchesQuery = item.concept.name
      .toLowerCase()
      .includes(query.toLowerCase());
    const matchesCategory =
      category === 'All' || item.concept.category === category;
    const matchesTag = tag === 'All' || item.concept.tags.includes(tag);
    return matchesQuery && matchesCategory && matchesTag;
  });
  $: selectedExploreConcept.set(selected);

  onMount(async () => {
    concepts = await listExploreConcepts();
    if (concepts[0]) await selectConcept(concepts[0].concept.slug);
    isLoading = false;
  });

  async function selectConcept(slug: string): Promise<void> {
    selected = await getExploreConcept(slug);
    selectedRelated = new Set(
      selected.related_concepts.map((concept) => concept.name)
    );
    message = null;
  }

  function toggleRelated(name: string): void {
    const next = new Set(selectedRelated);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    selectedRelated = next;
  }

  async function saveLinks(): Promise<void> {
    if (!selected) return;
    isSaving = true;
    message = null;
    try {
      await saveRelatedConcepts(
        selected.concept.slug,
        Array.from(selectedRelated)
      );
      selected = await getExploreConcept(selected.concept.slug);
      concepts = await listExploreConcepts();
      message = 'Related concepts saved in Markdown.';
    } finally {
      isSaving = false;
    }
  }
</script>

<section
  class="grid min-h-[calc(100vh-4rem)] grid-cols-1 lg:grid-cols-[320px_minmax(0,1fr)_360px]"
>
  <aside
    class="border-b border-border bg-background/55 p-4 lg:border-b-0 lg:border-r"
  >
    <div>
      <p class="text-xs font-medium uppercase text-accent">Knowledge Engine</p>
      <h1 class="mt-2 text-2xl font-semibold text-foreground">Explore</h1>
    </div>

    <label
      class="mt-5 flex h-10 items-center gap-2 rounded-md border border-border bg-muted/25 px-3 text-sm text-muted-foreground focus-within:border-accent/45"
    >
      <Search size={15} />
      <input
        bind:value={query}
        class="min-w-0 flex-1 bg-transparent text-foreground outline-none placeholder:text-muted-foreground"
        placeholder="Search concepts"
      />
    </label>

    <div class="mt-4 grid grid-cols-2 gap-2">
      <select
        bind:value={category}
        class="h-9 rounded-md border border-border bg-background px-2 text-sm"
      >
        {#each categories as option}
          <option>{option}</option>
        {/each}
      </select>
      <select
        bind:value={tag}
        class="h-9 rounded-md border border-border bg-background px-2 text-sm"
      >
        {#each tags as option}
          <option>{option}</option>
        {/each}
      </select>
    </div>

    <div class="mt-5 space-y-2">
      {#if isLoading}
        <p class="text-sm text-muted-foreground">Loading concepts...</p>
      {:else if filtered.length === 0}
        <p class="text-sm text-muted-foreground">No concepts found.</p>
      {:else}
        {#each filtered as item}
          <button
            class={[
              'w-full rounded-md border px-3 py-3 text-left transition',
              selected?.concept.slug === item.concept.slug
                ? 'border-accent/45 bg-accent/10'
                : 'border-border bg-muted/20 hover:bg-muted/35'
            ]}
            type="button"
            on:click={() => selectConcept(item.concept.slug)}
          >
            <span class="block truncate text-sm font-medium text-foreground"
              >{item.concept.name}</span
            >
            <span class="mt-1 block text-xs text-muted-foreground">
              {item.concept.category || 'Uncategorized'}
            </span>
          </button>
        {/each}
      {/if}
    </div>
  </aside>

  <main class="min-w-0 border-b border-border p-5 lg:border-b-0 lg:border-r">
    {#if selected}
      <div class="border-b border-border pb-5">
        <p class="text-xs font-medium uppercase text-accent">
          Selected Concept
        </p>
        <h2 class="mt-2 text-3xl font-semibold text-foreground">
          {selected.concept.name}
        </h2>
        <p class="mt-3 text-sm leading-6 text-muted-foreground">
          {selected.description || 'No description yet.'}
        </p>
      </div>

      <div class="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="p-4">
          <p class="text-xs text-muted-foreground">Category</p>
          <p class="mt-2 text-sm font-medium text-foreground">
            {selected.concept.category || 'Empty'}
          </p>
        </Card>
        <Card className="p-4">
          <p class="text-xs text-muted-foreground">Papers</p>
          <p class="mt-2 text-sm font-medium text-foreground">
            {selected.related_papers.length}
          </p>
        </Card>
        <Card className="p-4">
          <p class="text-xs text-muted-foreground">Concepts</p>
          <p class="mt-2 text-sm font-medium text-foreground">
            {selected.related_concepts.length}
          </p>
        </Card>
        <Card className="p-4">
          <p class="text-xs text-muted-foreground">Projects</p>
          <p class="mt-2 text-sm font-medium text-foreground">
            {selected.related_projects.length}
          </p>
        </Card>
      </div>

      <Card className="mt-5 p-5">
        <div
          class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
        >
          <div>
            <h3 class="text-base font-semibold text-foreground">
              Link Concept
            </h3>
            <p class="mt-2 text-sm text-muted-foreground">
              Relations are written to this Concept Markdown note.
            </p>
          </div>
          <button
            class="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-accent px-4 text-sm font-medium text-accent-foreground transition hover:bg-accent/90 disabled:opacity-60"
            type="button"
            disabled={isSaving}
            on:click={saveLinks}
          >
            <Link2 size={16} />
            Save Links
          </button>
        </div>

        <div class="mt-5 grid gap-3 md:grid-cols-2">
          {#each concepts.filter((item) => item.concept.name !== selected?.concept.name) as item}
            <label
              class="flex cursor-pointer items-start gap-3 rounded-md border border-border bg-background/35 px-3 py-3"
            >
              <input
                class="mt-1"
                type="checkbox"
                checked={selectedRelated.has(item.concept.name)}
                on:change={() => toggleRelated(item.concept.name)}
              />
              <span>
                <span class="block text-sm font-medium text-foreground"
                  >{item.concept.name}</span
                >
                <span class="mt-1 block text-xs text-muted-foreground">
                  {item.concept.category || 'Uncategorized'}
                </span>
              </span>
            </label>
          {/each}
        </div>

        {#if message}
          <p class="mt-4 text-sm text-muted-foreground">{message}</p>
        {/if}
      </Card>
    {:else}
      <p class="text-sm text-muted-foreground">
        Select a concept to explore relations.
      </p>
    {/if}
  </main>

  <aside class="bg-background/45 p-5">
    {#if selected}
      <h2 class="text-base font-semibold text-foreground">Relations</h2>

      <section class="mt-5">
        <h3 class="mb-3 text-xs font-medium uppercase text-muted-foreground">
          Related Papers
        </h3>
        <div class="space-y-2">
          {#each selected.related_papers as paper}
            <a
              class="block rounded-md border border-border bg-muted/20 px-3 py-2 text-sm text-foreground hover:border-accent/40"
              href={`/workspace?open=${encodeURIComponent(`paper:${paper.id}`)}`}
            >
              {paper.filename}
            </a>
          {:else}
            <p class="text-sm text-muted-foreground">No related papers.</p>
          {/each}
        </div>
      </section>

      <section class="mt-5">
        <h3 class="mb-3 text-xs font-medium uppercase text-muted-foreground">
          Related Concepts
        </h3>
        <div class="space-y-2">
          {#each selected.related_concepts as concept}
            <button
              class="block w-full rounded-md border border-border bg-muted/20 px-3 py-2 text-left text-sm text-foreground hover:border-accent/40"
              type="button"
              on:click={() => selectConcept(concept.slug)}
            >
              {concept.name}
            </button>
          {:else}
            <p class="text-sm text-muted-foreground">No related concepts.</p>
          {/each}
        </div>
      </section>

      <section class="mt-5">
        <h3 class="mb-3 text-xs font-medium uppercase text-muted-foreground">
          Related Projects
        </h3>
        <div class="space-y-2">
          {#each selected.related_projects as project}
            <a
              class="block rounded-md border border-border bg-muted/20 px-3 py-2 text-sm text-foreground hover:border-accent/40"
              href={`/workspace?open=${encodeURIComponent(`project:${project}`)}`}
            >
              {project}
            </a>
          {:else}
            <p class="text-sm text-muted-foreground">No related projects.</p>
          {/each}
        </div>
      </section>

      <section class="mt-5">
        <h3 class="mb-3 text-xs font-medium uppercase text-muted-foreground">
          Brainstorm Notes
        </h3>
        <div class="space-y-2">
          {#each selected.brainstorm_notes as note}
            <a
              class="block rounded-md border border-border bg-muted/20 px-3 py-2 text-sm text-foreground hover:border-accent/40"
              href={`/workspace?open=${encodeURIComponent(`brainstorm:${note}`)}`}
            >
              {note}
            </a>
          {:else}
            <p class="text-sm text-muted-foreground">No brainstorm notes.</p>
          {/each}
        </div>
      </section>
    {/if}
  </aside>
</section>
