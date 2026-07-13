<script lang="ts">
  import type { WorkspacePanelContext } from '$lib/features/workspace/types/panels';

  type Props = {
    context: WorkspacePanelContext;
  };

  let { context }: Props = $props();

  let metadata = $derived(context.detail?.metadata ?? {});

  function fmtDate(value: string | undefined): string {
    if (!value) return '—';
    const date = new Date(value.trim());
    if (Number.isNaN(date.getTime())) return value.trim();
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  let status = $derived((metadata.status ?? '').trim());
</script>

<dl class="grid gap-2.5 text-sm">
  <div class="flex items-baseline justify-between gap-3">
    <dt class="text-xs text-muted-foreground">Created</dt>
    <dd class="text-xs text-foreground">{fmtDate(metadata.created)}</dd>
  </div>
  <div class="flex items-baseline justify-between gap-3">
    <dt class="text-xs text-muted-foreground">Modified</dt>
    <dd class="text-xs text-foreground">{fmtDate(metadata.updated)}</dd>
  </div>
  {#if status}
    <div class="flex items-baseline justify-between gap-3">
      <dt class="text-xs text-muted-foreground">Status</dt>
      <dd class="text-xs capitalize text-foreground">{status}</dd>
    </div>
  {/if}
</dl>
