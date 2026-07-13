<script lang="ts">
  type Props = {
    open: boolean;
    title: string;
    message: string;
    confirmLabel?: string;
    danger?: boolean;
    busy?: boolean;
    onConfirm: () => void;
    onCancel: () => void;
  };

  let {
    open,
    title,
    message,
    confirmLabel = 'Confirm',
    danger = true,
    busy = false,
    onConfirm,
    onCancel
  }: Props = $props();

  function onKeydown(event: KeyboardEvent): void {
    if (open && event.key === 'Escape') onCancel();
  }
</script>

<svelte:window onkeydown={onKeydown} />

{#if open}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <button
      type="button"
      class="absolute inset-0 bg-black/50"
      aria-label="Cancel"
      onclick={onCancel}
    ></button>
    <div
      class="relative z-10 w-full max-w-sm rounded-lg border border-border bg-background p-5 shadow-xl"
      role="dialog"
      aria-modal="true"
    >
      <h2 class="text-base font-semibold text-foreground">{title}</h2>
      <p class="mt-2 text-sm leading-relaxed text-muted-foreground">{message}</p>
      <div class="mt-5 flex justify-end gap-2">
        <button class="ros-btn-ghost" type="button" onclick={onCancel}>
          Cancel
        </button>
        <button
          class={danger
            ? 'inline-flex h-8 items-center rounded-md bg-entity-review px-3 text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-50'
            : 'inline-flex h-8 items-center rounded-md bg-accent px-3 text-xs font-semibold text-accent-foreground transition hover:bg-accent/90 disabled:opacity-50'}
          type="button"
          disabled={busy}
          onclick={onConfirm}
        >
          {confirmLabel}
        </button>
      </div>
    </div>
  </div>
{/if}
