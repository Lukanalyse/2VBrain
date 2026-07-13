<script lang="ts">
  import { AlertTriangle } from '@lucide/svelte';
  import { createEventDispatcher } from 'svelte';

  import type {
    DuplicateStrategy,
    LibraryImportConflict
  } from '$lib/features/library/types/library';

  export let conflict: LibraryImportConflict;

  const dispatch = createEventDispatcher<{ resolve: DuplicateStrategy }>();
</script>

<div
  class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 backdrop-blur-sm"
>
  <section
    class="w-full max-w-md rounded-lg border border-border bg-background p-5 shadow-panel"
  >
    <div class="flex items-start gap-3">
      <div
        class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-border bg-muted/50 text-accent"
      >
        <AlertTriangle size={18} strokeWidth={1.8} />
      </div>
      <div class="min-w-0">
        <h2 class="text-base font-semibold text-foreground">
          Already imported
        </h2>
        <p class="mt-2 text-sm leading-6 text-muted-foreground">
          {conflict.existing_item.original_filename} already exists in the Research
          Library.
        </p>
      </div>
    </div>

    <div class="mt-6 grid gap-2 sm:grid-cols-3">
      <button
        class="h-10 rounded-md border border-border bg-muted/30 px-3 text-sm text-muted-foreground transition hover:text-foreground"
        type="button"
        on:click={() => dispatch('resolve', 'replace')}
      >
        Replace
      </button>
      <button
        class="h-10 rounded-md bg-accent px-3 text-sm font-medium text-accent-foreground transition hover:bg-accent/90"
        type="button"
        on:click={() => dispatch('resolve', 'keep_both')}
      >
        Keep both
      </button>
      <button
        class="h-10 rounded-md border border-border bg-background/40 px-3 text-sm text-muted-foreground transition hover:text-foreground"
        type="button"
        on:click={() => dispatch('resolve', 'cancel')}
      >
        Cancel
      </button>
    </div>
  </section>
</div>
