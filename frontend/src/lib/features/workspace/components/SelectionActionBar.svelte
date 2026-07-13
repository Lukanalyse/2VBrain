<script lang="ts">
  import type { Component } from 'svelte';

  export type SelectionAction = {
    id: string;
    label: string;
    icon: Component;
    /** Tailwind text-color class for the icon (entity identity color). */
    iconClass?: string;
    run: (text: string) => void | Promise<void>;
  };

  type Props = {
    /**
     * Root element that scopes where selections are picked up. Only text
     * selected inside this element triggers the bar. When null the bar stays
     * hidden.
     */
    root: HTMLElement | null;
    actions: SelectionAction[];
  };

  let { root, actions }: Props = $props();

  let visible = $state(false);
  let busy = $state(false);
  let x = $state(0);
  let y = $state(0);
  let selectedText = $state('');
  let bar: HTMLDivElement | null = $state(null);

  /**
   * Reads the current selection from either the focused textarea inside the
   * root (today's reading notes) or the DOM range (the future PDF reader).
   */
  function readSelection(): string {
    if (!root) return '';
    const active = document.activeElement;
    if (
      active instanceof HTMLTextAreaElement &&
      root.contains(active) &&
      active.selectionStart !== active.selectionEnd
    ) {
      return active.value.slice(active.selectionStart, active.selectionEnd);
    }
    const selection = window.getSelection();
    if (selection && selection.rangeCount > 0 && !selection.isCollapsed) {
      const range = selection.getRangeAt(0);
      if (root.contains(range.commonAncestorContainer)) {
        return selection.toString();
      }
    }
    return '';
  }

  function clamp(value: number, min: number, max: number): number {
    return Math.min(Math.max(value, min), max);
  }

  function showAt(pointerX: number, pointerY: number, text: string): void {
    selectedText = text;
    // Position just above the pointer, kept inside the viewport.
    const margin = 12;
    x = clamp(pointerX, margin, window.innerWidth - margin);
    y = clamp(pointerY - margin, margin, window.innerHeight - margin);
    visible = true;
  }

  function handlePointerUp(event: PointerEvent): void {
    const text = readSelection().trim();
    if (!text) {
      visible = false;
      return;
    }
    showAt(event.clientX, event.clientY, text);
  }

  function handleKeyUp(event: KeyboardEvent): void {
    // Only react to selection-affecting keys (Shift + arrows / Ctrl+A).
    if (!event.shiftKey && event.key !== 'a') return;
    const text = readSelection().trim();
    if (!text) {
      visible = false;
      return;
    }
    const active = document.activeElement as HTMLElement | null;
    const rect = active?.getBoundingClientRect();
    if (rect) showAt(rect.left + rect.width / 2, rect.top, text);
  }

  function handleDocumentPointerDown(event: PointerEvent): void {
    if (bar && event.target instanceof Node && bar.contains(event.target)) {
      return; // clicking the bar itself must not dismiss it
    }
    visible = false;
  }

  function handleKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') visible = false;
  }

  function hide(): void {
    visible = false;
  }

  async function trigger(action: SelectionAction): Promise<void> {
    if (busy || !selectedText) return;
    busy = true;
    try {
      await action.run(selectedText);
    } finally {
      busy = false;
      visible = false;
      window.getSelection()?.removeAllRanges();
    }
  }

  // Bind listeners to the current root; rebind if the root element changes.
  $effect(() => {
    const el = root;
    if (!el) return;
    el.addEventListener('pointerup', handlePointerUp);
    el.addEventListener('keyup', handleKeyUp);
    document.addEventListener('pointerdown', handleDocumentPointerDown, true);
    document.addEventListener('keydown', handleKeydown);
    window.addEventListener('scroll', hide, true);
    window.addEventListener('resize', hide);
    return () => {
      el.removeEventListener('pointerup', handlePointerUp);
      el.removeEventListener('keyup', handleKeyUp);
      document.removeEventListener(
        'pointerdown',
        handleDocumentPointerDown,
        true
      );
      document.removeEventListener('keydown', handleKeydown);
      window.removeEventListener('scroll', hide, true);
      window.removeEventListener('resize', hide);
    };
  });
</script>

{#if visible && actions.length}
  <div
    bind:this={bar}
    class="fixed z-50 flex -translate-x-1/2 -translate-y-full items-center gap-0.5 rounded-lg border border-border bg-background p-1 shadow-lg"
    style="left: {x}px; top: {y}px;"
    role="toolbar"
    aria-label="Selection actions"
  >
    {#each actions as action (action.id)}
      <button
        type="button"
        class="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium text-foreground transition hover:bg-muted/60 disabled:opacity-50"
        disabled={busy}
        onclick={() => trigger(action)}
      >
        <action.icon size={14} class={action.iconClass ?? 'text-accent'} />
        {action.label}
      </button>
    {/each}
  </div>
{/if}
