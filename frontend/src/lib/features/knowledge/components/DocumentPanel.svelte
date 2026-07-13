<script lang="ts">
  import { ExternalLink, FileText } from '@lucide/svelte';

  import { openPdf } from '$lib/features/knowledge/services/knowledgeApi';
  import type { KnowledgeItem } from '$lib/features/knowledge/types/knowledge';

  export let item: KnowledgeItem;

  let message: string | null = null;

  function formatDate(value: string): string {
    const hasTimezone = /(?:z|[+-]\d{2}:?\d{2})$/i.test(value);
    return new Intl.DateTimeFormat(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(new Date(hasTimezone ? value : `${value}Z`));
  }

  async function handleOpenPdf(): Promise<void> {
    message = null;
    try {
      await openPdf(item.id);
      message = 'PDF opened with the system reader.';
    } catch (error) {
      message = error instanceof Error ? error.message : 'Unable to open PDF.';
    }
  }
</script>

<aside
  class="border-b border-border bg-background/45 p-5 lg:w-80 lg:border-b-0 lg:border-r"
>
  <div class="flex items-start gap-3">
    <div
      class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-border bg-muted/50 text-accent"
    >
      <FileText size={18} strokeWidth={1.8} />
    </div>
    <div class="min-w-0">
      <p class="text-xs font-medium uppercase text-accent">Document</p>
      <h1 class="mt-2 truncate text-lg font-semibold text-foreground">
        {item.filename}
      </h1>
    </div>
  </div>

  <dl class="mt-6 space-y-4">
    <div>
      <dt class="text-xs text-muted-foreground">Status</dt>
      <dd class="mt-1 text-sm font-medium capitalize text-foreground">
        {item.status}
      </dd>
    </div>
    <div>
      <dt class="text-xs text-muted-foreground">Imported</dt>
      <dd class="mt-1 text-sm text-foreground">
        {formatDate(item.imported_at)}
      </dd>
    </div>
    <div>
      <dt class="text-xs text-muted-foreground">PDF path</dt>
      <dd class="mt-1 break-words text-xs leading-5 text-foreground">
        {item.file_path}
      </dd>
    </div>
  </dl>

  <button
    class="mt-6 inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-accent px-3 text-sm font-medium text-accent-foreground transition hover:bg-accent/90"
    type="button"
    on:click={handleOpenPdf}
  >
    <ExternalLink size={16} />
    Open PDF
  </button>

  {#if message}
    <p class="mt-3 text-xs leading-5 text-muted-foreground">{message}</p>
  {/if}
</aside>
