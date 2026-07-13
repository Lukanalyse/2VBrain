<script lang="ts">
  import { X } from '@lucide/svelte';
  import { createEventDispatcher } from 'svelte';

  import { createConcept } from '$lib/features/concepts/services/conceptsApi';
  import type {
    Concept,
    ConceptCreate
  } from '$lib/features/concepts/types/concept';

  const dispatch = createEventDispatcher<{ created: Concept; close: void }>();

  let name = '';
  let description = '';
  let category = '';
  let tags = '';
  let errorMessage: string | null = null;
  let isSaving = false;

  async function submit(): Promise<void> {
    errorMessage = null;
    isSaving = true;
    const payload: ConceptCreate = {
      name,
      description,
      category,
      tags: tags
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean)
    };

    try {
      const concept = await createConcept(payload);
      dispatch('created', concept);
    } catch (error) {
      errorMessage =
        error instanceof Error ? error.message : 'Unable to create concept.';
    } finally {
      isSaving = false;
    }
  }
</script>

<div
  class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 backdrop-blur-sm"
>
  <section
    class="w-full max-w-xl rounded-lg border border-border bg-background p-5 shadow-panel"
  >
    <div class="flex items-center justify-between gap-4">
      <div>
        <p class="text-xs font-medium uppercase text-accent">Knowledge Model</p>
        <h2 class="mt-1 text-lg font-semibold text-foreground">New Concept</h2>
      </div>
      <button
        class="flex h-8 w-8 items-center justify-center rounded-md border border-border text-muted-foreground transition hover:text-foreground"
        type="button"
        aria-label="Close"
        on:click={() => dispatch('close')}
      >
        <X size={15} />
      </button>
    </div>

    <div class="mt-5 space-y-4">
      <label class="block">
        <span class="text-sm font-medium text-foreground">Name</span>
        <input
          bind:value={name}
          class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm text-foreground outline-none focus:border-accent/50"
          placeholder="Thompson Sampling"
        />
      </label>
      <label class="block">
        <span class="text-sm font-medium text-foreground">Description</span>
        <textarea
          bind:value={description}
          class="mt-2 min-h-24 w-full resize-none rounded-md border border-border bg-background/50 px-3 py-2 text-sm text-foreground outline-none focus:border-accent/50"
          placeholder="Short explanation of the concept"
        ></textarea>
      </label>
      <div class="grid gap-4 sm:grid-cols-2">
        <label class="block">
          <span class="text-sm font-medium text-foreground">Category</span>
          <input
            bind:value={category}
            class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm text-foreground outline-none focus:border-accent/50"
            placeholder="Algorithm"
          />
        </label>
        <label class="block">
          <span class="text-sm font-medium text-foreground">Tags</span>
          <input
            bind:value={tags}
            class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm text-foreground outline-none focus:border-accent/50"
            placeholder="bandits, bayesian"
          />
        </label>
      </div>
    </div>

    {#if errorMessage}
      <p
        class="mt-4 rounded-md border border-border bg-muted/25 px-3 py-2 text-sm text-muted-foreground"
      >
        {errorMessage}
      </p>
    {/if}

    <div class="mt-6 flex justify-end gap-2">
      <button
        class="h-10 rounded-md border border-border bg-muted/25 px-4 text-sm text-muted-foreground transition hover:text-foreground"
        type="button"
        on:click={() => dispatch('close')}
      >
        Cancel
      </button>
      <button
        class="h-10 rounded-md bg-accent px-4 text-sm font-medium text-accent-foreground transition hover:bg-accent/90 disabled:opacity-60"
        type="button"
        disabled={isSaving}
        on:click={submit}
      >
        Create Concept
      </button>
    </div>
  </section>
</div>
