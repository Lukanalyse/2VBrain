<script lang="ts">
  import { onMount } from 'svelte';

  import { getRelations } from '$lib/features/linking/services/linkingApi';
  import type {
    LinkableObject,
    LinkableType,
    ObjectRelations
  } from '$lib/features/linking/types/linking';

  export let sourceId: string;

  let relations: ObjectRelations | null = null;
  let isLoading = true;
  let errorMessage: string | null = null;

  const typeLabels: Record<LinkableType, string> = {
    paper: 'Papers',
    concept: 'Concepts',
    project: 'Projects',
    brainstorm: 'Brainstorm Notes',
    review: 'Literature Reviews',
    note: 'Notes'
  };

  const types: LinkableType[] = [
    'paper',
    'concept',
    'project',
    'brainstorm',
    'review',
    'note'
  ];

  export async function refresh(): Promise<void> {
    isLoading = true;
    errorMessage = null;
    try {
      relations = await getRelations(sourceId);
    } catch (error) {
      errorMessage =
        error instanceof Error ? error.message : 'Unable to load relations.';
    } finally {
      isLoading = false;
    }
  }

  function hrefFor(item: LinkableObject): string {
    return `/workspace?open=${encodeURIComponent(item.id)}`;
  }

  onMount(refresh);
</script>

<section class="space-y-5">
  {#if isLoading}
    <p class="text-sm text-muted-foreground">Loading relations...</p>
  {:else if errorMessage || !relations}
    <p class="text-sm text-muted-foreground">{errorMessage}</p>
  {:else}
    <div>
      <p class="text-xs font-medium uppercase text-accent">Relations</p>
      <h2 class="mt-1 text-base font-semibold text-foreground">
        {relations.source.title}
      </h2>
    </div>

    <div class="space-y-5">
      {#each types as type}
        <section>
          <h3 class="mb-3 text-xs font-medium uppercase text-muted-foreground">
            Linked {typeLabels[type]}
          </h3>
          <div class="space-y-2">
            {#each relations.outgoing[type] as item}
              <a
                class="block rounded-md border border-border bg-muted/20 px-3 py-2 text-sm text-foreground transition hover:border-accent/40"
                href={hrefFor(item)}
              >
                {item.title}
              </a>
            {:else}
              <p class="text-sm text-muted-foreground">
                No linked {typeLabels[type].toLowerCase()}.
              </p>
            {/each}
          </div>
        </section>
      {/each}
    </div>

    <div class="border-t border-border pt-5">
      <h3 class="mb-3 text-xs font-medium uppercase text-muted-foreground">
        Backlinks
      </h3>
      <div class="space-y-2">
        {#each types.flatMap((type) => relations?.incoming[type] ?? []) as item}
          <a
            class="block rounded-md border border-border bg-background/35 px-3 py-2 text-sm text-foreground transition hover:border-accent/40"
            href={hrefFor(item)}
          >
            {item.title}
          </a>
        {:else}
          <p class="text-sm text-muted-foreground">No backlinks yet.</p>
        {/each}
      </div>
    </div>
  {/if}
</section>
