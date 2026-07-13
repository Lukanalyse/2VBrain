<script lang="ts">
  import type { SaveState } from '$lib/features/knowledge/types/knowledge';

  export let content: string;
  export let saveState: SaveState;

  function labelForState(state: SaveState): string {
    if (state === 'saving') return 'Saving...';
    if (state === 'unsaved') return 'Unsaved changes';
    if (state === 'error') return 'Save failed';
    return 'Saved';
  }
</script>

<div id="notes" class="flex min-h-0 flex-1 flex-col">
  <div
    class="flex items-center justify-between gap-4 border-b border-border px-5 py-3"
  >
    <div>
      <p class="text-xs font-medium uppercase text-accent">Markdown</p>
      <h2 class="mt-1 text-sm font-semibold text-foreground">Notes</h2>
    </div>
    <span
      class={[
        'rounded-md border px-2 py-1 text-xs',
        saveState === 'saved'
          ? 'border-accent/35 bg-accent/10 text-accent'
          : 'border-border bg-muted/30 text-muted-foreground'
      ]}
    >
      {labelForState(saveState)}
    </span>
  </div>

  <textarea
    bind:value={content}
    class="min-h-[520px] flex-1 resize-none bg-background/35 px-5 py-5 font-mono text-sm leading-7 text-foreground outline-none placeholder:text-muted-foreground lg:min-h-0"
    spellcheck="true"
  ></textarea>
</div>
