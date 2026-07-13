<script lang="ts">
  import { Brain } from '@lucide/svelte';

  import type { Concept } from '$lib/features/concepts/types/concept';

  export let concept: Concept;
</script>

<a
  class="block rounded-lg border border-border bg-muted/25 p-4 shadow-panel transition hover:border-accent/40 hover:bg-muted/35"
  href={`/workspace?open=${encodeURIComponent(`concept:${concept.slug}`)}`}
>
  <div class="flex items-start gap-3">
    <div
      class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-border bg-background/50 text-accent"
    >
      <Brain size={18} strokeWidth={1.8} />
    </div>
    <div class="min-w-0 flex-1">
      <h3 class="truncate text-sm font-medium text-foreground">
        {concept.name}
      </h3>
      <p class="mt-1 text-xs text-muted-foreground">
        {concept.category || 'Uncategorized'}
      </p>
      <div class="mt-4 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
        <div class="rounded-md border border-border bg-background/35 px-2 py-2">
          {concept.linked_papers_count} Papers
        </div>
        <div class="rounded-md border border-border bg-background/35 px-2 py-2">
          {concept.linked_concepts_count} Concepts
        </div>
      </div>
    </div>
  </div>
</a>
