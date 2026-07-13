<script lang="ts">
  import { CheckCircle2, Database, Upload } from '@lucide/svelte';

  import DuplicateImportDialog from '$lib/features/library/components/DuplicateImportDialog.svelte';
  import LibraryExplorer from '$lib/features/library/components/LibraryExplorer.svelte';
  import MetadataPreviewModal from '$lib/features/library/components/MetadataPreviewModal.svelte';
  import PdfDropzone from '$lib/features/library/components/PdfDropzone.svelte';
  import {
    importPdf,
    LibraryConflictError,
    previewPdfMetadata
  } from '$lib/features/library/services/libraryApi';
  import type {
    DuplicateStrategy,
    LibraryImportConflict,
    PdfMetadataPreview
  } from '$lib/features/library/types/library';

  let explorer = $state<LibraryExplorer>();
  let dropzone = $state<PdfDropzone>();
  let isImporting = $state(false);
  let importState = $state<'idle' | 'importing' | 'success' | 'error'>('idle');
  let errorMessage = $state<string | null>(null);
  let successMessage = $state<string | null>(null);
  let pendingFile = $state<File | null>(null);
  let pendingStrategy = $state<DuplicateStrategy>('cancel');
  let pendingMetadata = $state<PdfMetadataPreview | null>(null);
  let duplicateConflict = $state<LibraryImportConflict | null>(null);
  let duplicateFile = $state<File | null>(null);

  $effect(() => {
    importState = isImporting
      ? 'importing'
      : errorMessage
        ? 'error'
        : successMessage
          ? 'success'
          : 'idle';
  });

  async function handleFiles(event: CustomEvent<FileList>): Promise<void> {
    const file = event.detail.item(0);
    if (file) await previewSelectedFile(file);
  }

  async function previewSelectedFile(
    file: File,
    strategy: DuplicateStrategy = 'cancel'
  ): Promise<void> {
    errorMessage = null;
    successMessage = null;
    isImporting = true;
    try {
      if (
        !file.name.toLowerCase().endsWith('.pdf') &&
        file.type !== 'application/pdf'
      ) {
        throw new Error('Only PDF files are supported.');
      }
      pendingMetadata = await previewPdfMetadata(file);
      pendingFile = file;
      pendingStrategy = strategy;
    } catch (error) {
      errorMessage =
        error instanceof Error ? error.message : 'Unable to preview this PDF.';
    } finally {
      isImporting = false;
    }
  }

  async function importSelectedFile(
    metadata: PdfMetadataPreview
  ): Promise<void> {
    if (!pendingFile) return;
    errorMessage = null;
    successMessage = null;
    isImporting = true;
    try {
      await importPdf(pendingFile, pendingStrategy, metadata);
      pendingFile = null;
      pendingMetadata = null;
      await explorer?.load();
      successMessage = 'Paper imported into your Library.';
    } catch (error) {
      if (error instanceof LibraryConflictError) {
        duplicateConflict = error.conflict;
        duplicateFile = error.file;
        pendingMetadata = null;
      } else {
        errorMessage =
          error instanceof Error ? error.message : 'Unable to import this PDF.';
      }
    } finally {
      isImporting = false;
    }
  }

  async function resolveDuplicate(
    event: CustomEvent<DuplicateStrategy>
  ): Promise<void> {
    const strategy = event.detail;
    const file = duplicateFile;
    duplicateConflict = null;
    duplicateFile = null;
    if (!file || strategy === 'cancel') return;
    await previewSelectedFile(file, strategy);
  }
</script>

<section class="library-system min-h-[calc(100vh-4rem)]">
  <div class="library-grid" aria-hidden="true"></div>
  <div class="relative z-[1] mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-6xl flex-col px-5 py-7 lg:px-8">
    <header class="library-header flex flex-wrap items-center justify-between gap-5 border-b border-border pb-5">
      <div class="flex min-w-0 items-center gap-4">
        <span class="library-core" aria-hidden="true">
          <Database size={20} strokeWidth={1.7} />
        </span>
        <div>
          <p class="text-[0.68rem] font-semibold uppercase text-accent">
            Memory module
          </p>
          <h1 class="mt-1 text-2xl font-semibold text-foreground">
            Library
          </h1>
          <p class="mt-1 max-w-2xl text-sm text-muted-foreground">
            Complete index · sources, ideas and archived research
          </p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <span class="library-status hidden items-center gap-2 text-xs text-muted-foreground sm:inline-flex">
          <span class="h-1.5 w-1.5 bg-accent"></span>
          Index online
        </span>
        <button
          class="flex h-9 items-center gap-2 rounded-md bg-accent px-3 text-sm font-medium text-accent-foreground transition hover:bg-accent/90"
          type="button"
          onclick={() => dropzone?.openFilePicker()}
        >
          <Upload size={15} />
          Import PDF
        </button>
      </div>
    </header>

    {#if successMessage}
      <div
        class="mt-4 flex items-center gap-2 rounded-md border border-accent/40 bg-accent/10 px-3 py-2 text-sm text-accent"
      >
        <CheckCircle2 size={15} />
        {successMessage}
      </div>
    {:else if errorMessage}
      <div
        class="mt-4 rounded-md border border-border bg-muted/25 px-3 py-2 text-sm text-muted-foreground"
      >
        {errorMessage}
      </div>
    {/if}

    <div class="mt-3 min-h-0 flex-1">
      <LibraryExplorer bind:this={explorer} />
    </div>
  </div>
</section>

<div class="sr-only">
  <PdfDropzone
    bind:this={dropzone}
    {isImporting}
    {importState}
    on:files={handleFiles}
  />
</div>

{#if duplicateConflict}
  <DuplicateImportDialog
    conflict={duplicateConflict}
    on:resolve={resolveDuplicate}
  />
{/if}

<style>
  .library-system {
    position: relative;
    overflow: hidden;
    background: hsl(var(--background));
  }

  .library-grid {
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-image:
      linear-gradient(hsl(var(--foreground) / 0.028) 1px, transparent 1px),
      linear-gradient(90deg, hsl(var(--foreground) / 0.028) 1px, transparent 1px);
    background-size: 32px 32px;
    mask-image: linear-gradient(to bottom, black, transparent 88%);
  }

  .library-header {
    position: relative;
  }

  .library-header::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    width: min(240px, 34%);
    height: 1px;
    background: hsl(var(--accent) / 0.72);
    box-shadow: 0 0 10px hsl(var(--accent) / 0.25);
  }

  .library-core {
    position: relative;
    display: inline-flex;
    width: 48px;
    height: 48px;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    border: 1px solid hsl(var(--accent) / 0.4);
    border-radius: 8px;
    color: hsl(var(--accent));
    background:
      linear-gradient(hsl(var(--foreground) / 0.05) 1px, transparent 1px),
      linear-gradient(90deg, hsl(var(--foreground) / 0.05) 1px, transparent 1px),
      hsl(var(--muted) / 0.25);
    background-size: 7px 7px;
    box-shadow: inset 0 0 18px hsl(var(--accent) / 0.06);
  }

  .library-core::before,
  .library-core::after {
    content: '';
    position: absolute;
    left: 10px;
    right: 10px;
    height: 3px;
    border-inline: 1px solid hsl(var(--muted-foreground) / 0.65);
  }

  .library-core::before {
    top: -4px;
  }

  .library-core::after {
    bottom: -4px;
  }

  .library-status {
    border-right: 1px solid hsl(var(--border));
    padding-right: 12px;
  }
</style>

{#if pendingMetadata && pendingFile}
  <MetadataPreviewModal
    metadata={pendingMetadata}
    filename={pendingFile.name}
    {isImporting}
    on:cancel={() => {
      pendingMetadata = null;
      pendingFile = null;
    }}
    on:import={(event) => importSelectedFile(event.detail)}
  />
{/if}
