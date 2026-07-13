<script lang="ts">
  import { FileText } from '@lucide/svelte';

  import type { LibraryItem } from '$lib/features/library/types/library';

  export let item: LibraryItem;

  function parseImportedAt(value: string): Date {
    const hasTimezone = /(?:z|[+-]\d{2}:?\d{2})$/i.test(value);
    return new Date(hasTimezone ? value : `${value}Z`);
  }

  function formatImportedAt(value: string): string {
    const date = parseImportedAt(value);
    const importedAt = date.getTime();
    const secondsAgo = Math.max(
      0,
      Math.floor((Date.now() - importedAt) / 1000)
    );

    if (secondsAgo < 60) return 'Imported just now';
    if (secondsAgo < 3600)
      return `Imported ${Math.floor(secondsAgo / 60)} min ago`;

    return `Imported ${new Intl.DateTimeFormat(undefined, {
      month: 'short',
      day: 'numeric'
    }).format(date)}`;
  }

  $: importedLabel = formatImportedAt(item.imported_at);
  $: statusLabel = item.status.charAt(0).toUpperCase() + item.status.slice(1);
</script>

<a
  class="block rounded-lg border border-border bg-muted/25 p-4 shadow-panel transition hover:border-accent/40 hover:bg-muted/35"
  href={`/workspace?open=paper:${item.id}`}
>
  <div class="flex items-start gap-3">
    <div
      class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-border bg-background/50 text-accent"
    >
      <FileText size={18} strokeWidth={1.8} />
    </div>
    <div class="min-w-0 flex-1">
      <h3 class="truncate text-sm font-medium text-foreground">
        {item.title || item.filename}
      </h3>
      {#if item.title}
        <p class="mt-1 truncate text-xs text-muted-foreground">
          {item.filename}
        </p>
      {/if}
      <p class="mt-1 text-xs text-muted-foreground">{importedLabel}</p>
      <div class="mt-3">
        <span
          class="rounded-md border border-border bg-background/45 px-2 py-1 text-xs text-muted-foreground"
        >
          {statusLabel}
        </span>
      </div>
    </div>
  </div>
</a>
