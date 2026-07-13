<script lang="ts">
  import { X } from '@lucide/svelte';

  // Native, autosave tag editor. Type + Enter (or comma) adds a chip and saves
  // immediately; the ✕ removes and saves; Backspace on an empty field removes
  // the last chip. No Save button — every mutation calls `onSave`.
  type Props = {
    tags: string[] | undefined | null;
    onSave: (tags: string[]) => Promise<void>;
    placeholder?: string;
  };

  let { tags, onSave, placeholder = 'Add a tag…' }: Props = $props();

  let chips = $state<string[]>([]);
  let draft = $state('');
  let saving = $state(false);
  let failed = $state(false);
  let syncKey = '';

  // Adopt the persisted tags whenever they change (object switch, refresh).
  // Optimistic updates set `syncKey` too, so a same-value refresh is a no-op.
  $effect(() => {
    const incoming = (tags ?? []).map((tag) => tag.trim()).filter(Boolean);
    const key = incoming.join('\0');
    if (key !== syncKey) {
      syncKey = key;
      chips = incoming;
    }
  });

  async function commit(next: string[]): Promise<void> {
    const previous = chips;
    chips = next;
    syncKey = next.join('\0');
    saving = true;
    failed = false;
    try {
      await onSave(next);
    } catch {
      chips = previous;
      syncKey = previous.join('\0');
      failed = true;
    } finally {
      saving = false;
    }
  }

  function addFromDraft(): void {
    const value = draft.trim().replace(/,+$/, '').trim();
    draft = '';
    if (!value) return;
    if (chips.some((chip) => chip.toLowerCase() === value.toLowerCase())) return;
    void commit([...chips, value]);
  }

  function removeAt(index: number): void {
    void commit(chips.filter((_, position) => position !== index));
  }

  function onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault();
      addFromDraft();
    } else if (event.key === 'Backspace' && draft === '' && chips.length) {
      event.preventDefault();
      removeAt(chips.length - 1);
    }
  }
</script>

<div
  class="flex flex-wrap items-center gap-1.5 rounded-md border border-border bg-background px-2 py-1.5 transition focus-within:border-accent/50"
  class:opacity-60={saving}
>
  {#each chips as tag, index (tag)}
    <span
      class="inline-flex items-center gap-1 rounded-full border border-border/70 bg-muted/40 py-0.5 pl-2 pr-1 text-[11px] font-medium leading-none text-foreground"
    >
      {tag}
      <button
        type="button"
        class="flex items-center rounded-full p-0.5 text-muted-foreground transition hover:bg-muted hover:text-foreground"
        aria-label={`Remove ${tag}`}
        onclick={() => removeAt(index)}
      >
        <X size={11} />
      </button>
    </span>
  {/each}
  <input
    bind:value={draft}
    class="h-6 min-w-[6rem] flex-1 bg-transparent text-xs text-foreground outline-none placeholder:text-muted-foreground"
    {placeholder}
    onkeydown={onKeydown}
    onblur={addFromDraft}
  />
</div>
{#if failed}
  <p class="mt-1 text-[11px] text-entity-review">Could not save tags — retry.</p>
{/if}
