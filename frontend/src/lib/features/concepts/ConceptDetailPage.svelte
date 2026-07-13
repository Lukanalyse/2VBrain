<script lang="ts">
  import { ArrowLeft, FileText } from '@lucide/svelte';
  import { onMount } from 'svelte';

  import Card from '$lib/components/ui/Card.svelte';
  import { getConcept } from '$lib/features/concepts/services/conceptsApi';
  import type { ConceptDetail } from '$lib/features/concepts/types/concept';
  import LinkPicker from '$lib/features/linking/components/LinkPicker.svelte';
  import RelationsPanel from '$lib/features/linking/components/RelationsPanel.svelte';

  export let slug: string;

  let detail: ConceptDetail | null = null;
  let errorMessage: string | null = null;
  let isLoading = true;
  let relationsPanel: RelationsPanel;

  onMount(async () => {
    try {
      detail = await getConcept(slug);
    } catch (error) {
      errorMessage =
        error instanceof Error ? error.message : 'Unable to load concept.';
    } finally {
      isLoading = false;
    }
  });
</script>

<section class="px-4 py-6 lg:px-8 lg:py-8">
  <div class="mx-auto w-full max-w-5xl space-y-6">
    <a
      class="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-muted/25 px-3 text-sm text-muted-foreground transition hover:text-foreground"
      href="/"
    >
      <ArrowLeft size={15} />
      Knowledge
    </a>

    {#if isLoading}
      <p class="text-sm text-muted-foreground">Loading concept...</p>
    {:else if errorMessage || !detail}
      <Card className="p-5 text-center">
        <h1 class="text-lg font-semibold text-foreground">
          Unable to open concept
        </h1>
        <p class="mt-2 text-sm text-muted-foreground">{errorMessage}</p>
      </Card>
    {:else}
      <div class="border-b border-border pb-5">
        <p class="text-xs font-medium uppercase text-accent">Concept</p>
        <h1 class="mt-2 text-3xl font-semibold text-foreground">
          {detail.concept.name}
        </h1>
        <p class="mt-3 text-sm text-muted-foreground">
          {detail.concept.category || 'Uncategorized'} · {detail.concept
            .markdown_path}
        </p>
      </div>

      <div class="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <Card className="p-5">
          <h2 class="text-base font-semibold text-foreground">References</h2>
          {#if detail.linked_papers.length === 0}
            <p class="mt-3 text-sm leading-6 text-muted-foreground">
              No papers linked yet.
            </p>
          {:else}
            <div class="mt-4 space-y-3">
              {#each detail.linked_papers as paper}
                <a
                  class="flex items-start gap-3 rounded-md border border-border bg-background/35 px-3 py-3 transition hover:border-accent/40"
                  href={`/workspace?open=${encodeURIComponent(`paper:${paper.id}`)}`}
                >
                  <FileText size={17} class="mt-0.5 text-accent" />
                  <div class="min-w-0">
                    <p class="truncate text-sm font-medium text-foreground">
                      {paper.filename}
                    </p>
                    <p class="mt-1 text-xs text-muted-foreground">
                      {paper.status}
                    </p>
                  </div>
                </a>
              {/each}
            </div>
          {/if}
        </Card>

        <Card className="p-5">
          <h2 class="text-base font-semibold text-foreground">Markdown</h2>
          <pre
            class="mt-4 max-h-[520px] overflow-auto whitespace-pre-wrap rounded-md border border-border bg-background/45 p-4 text-sm leading-7 text-muted-foreground">{detail.content}</pre>
        </Card>
      </div>

      <div class="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <LinkPicker
          sourceId={`concept:${detail.concept.slug}`}
          on:linked={() => relationsPanel?.refresh()}
        />
        <Card className="p-5">
          <RelationsPanel
            bind:this={relationsPanel}
            sourceId={`concept:${detail.concept.slug}`}
          />
        </Card>
      </div>
    {/if}
  </div>
</section>
