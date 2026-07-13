<script lang="ts">
  import { CheckCircle2, FileUp, Loader2 } from '@lucide/svelte';
  import { createEventDispatcher } from 'svelte';

  import { cn } from '$lib/utils';

  export let isImporting = false;
  export let importState: 'idle' | 'importing' | 'success' | 'error' = 'idle';

  const dispatch = createEventDispatcher<{ files: FileList }>();
  let isDragging = false;
  let fileInput: HTMLInputElement;

  function emitFiles(files: FileList | null): void {
    if (!files || files.length === 0) return;
    dispatch('files', files);
    if (fileInput) fileInput.value = '';
  }

  export function openFilePicker(): void {
    fileInput.showPicker?.();
    if (!fileInput.showPicker) fileInput.click();
  }
</script>

<div
  data-testid="pdf-dropzone"
  role="region"
  aria-label="PDF import dropzone"
  class={cn(
    'rounded-xl border border-dashed border-border bg-muted/20 px-6 py-12 text-center shadow-panel transition duration-150 sm:px-10 sm:py-16',
    isDragging && 'scale-[1.01] border-accent/80 bg-accent/10'
  )}
  on:dragenter|preventDefault={() => (isDragging = true)}
  on:dragover|preventDefault={() => (isDragging = true)}
  on:dragleave|preventDefault={() => (isDragging = false)}
  on:drop|preventDefault={(event) => {
    isDragging = false;
    emitFiles(event.dataTransfer?.files ?? null);
  }}
>
  <div
    class="mx-auto flex h-16 w-16 items-center justify-center rounded-xl border border-border bg-background/55 text-accent"
  >
    {#if isImporting}
      <Loader2 class="animate-spin" size={26} />
    {:else if importState === 'success'}
      <CheckCircle2 size={26} strokeWidth={1.8} />
    {:else}
      <FileUp size={26} strokeWidth={1.8} />
    {/if}
  </div>
  <h2 class="mt-6 text-2xl font-semibold text-foreground">
    {isDragging
      ? 'Drop to import'
      : isImporting
        ? 'Importing paper...'
        : 'Drop PDF Here'}
  </h2>
  <p class="mt-3 text-sm text-muted-foreground">or</p>
  <label
    class="relative mt-5 inline-flex h-10 cursor-pointer items-center justify-center overflow-hidden rounded-md bg-accent px-5 text-sm font-medium text-accent-foreground transition hover:bg-accent/90"
    class:pointer-events-none={isImporting}
    class:opacity-60={isImporting}
  >
    <span class="pointer-events-none">Import PDF</span>
    <input
      data-testid="pdf-file-input"
      bind:this={fileInput}
      class="absolute inset-0 z-10 cursor-pointer opacity-0"
      type="file"
      aria-label="Import PDF"
      accept="application/pdf,.pdf"
      disabled={isImporting}
      on:change={(event) => emitFiles(event.currentTarget.files)}
    />
  </label>
  <p class="mt-5 text-xs text-muted-foreground">Formats supported: PDF</p>

  {#if isImporting}
    <div
      class="mx-auto mt-6 h-2 w-full max-w-sm overflow-hidden rounded-full bg-background/70"
    >
      <div class="h-full w-2/3 animate-pulse rounded-full bg-accent"></div>
    </div>
  {/if}
</div>
