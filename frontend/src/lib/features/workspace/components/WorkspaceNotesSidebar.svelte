<script lang="ts">
  import { Copy, FileText, Pencil, Plus, Trash2 } from '@lucide/svelte';

  import type { WorkspaceNote } from '$lib/features/workspace/services/workspaceApi';

  type Props = {
    notes: WorkspaceNote[];
    activeNoteId: string;
    busy?: boolean;
    onSelect: (noteId: string) => void | Promise<void>;
    onCreate: (title: string) => void | Promise<void>;
    onRename: (noteId: string, title: string) => void | Promise<void>;
    onDuplicate: (noteId: string) => void | Promise<void>;
    onDelete: (noteId: string) => void | Promise<void>;
  };

  let {
    notes,
    activeNoteId,
    busy = false,
    onSelect,
    onCreate,
    onRename,
    onDuplicate,
    onDelete
  }: Props = $props();

  let creating = $state(false);
  let draftTitle = $state('');
  let editingNoteId = $state<string | null>(null);
  let editingTitle = $state('');

  function beginCreate(): void {
    creating = true;
    draftTitle = '';
  }

  async function confirmCreate(): Promise<void> {
    const title = draftTitle.trim();
    if (!title) return;
    await onCreate(title);
    creating = false;
    draftTitle = '';
  }

  function beginRename(note: WorkspaceNote): void {
    if (note.is_primary) return;
    editingNoteId = note.id;
    editingTitle = note.title;
  }

  async function confirmRename(): Promise<void> {
    const noteId = editingNoteId;
    const title = editingTitle.trim();
    if (!noteId || !title) return;
    await onRename(noteId, title);
    editingNoteId = null;
    editingTitle = '';
  }
</script>

<aside class="w-56 shrink-0 border-r border-border bg-background/50 p-3">
  <div class="flex items-center justify-between gap-2">
    <div>
      <p class="text-xs font-medium uppercase text-entity-note">Notes</p>
      <p class="mt-0.5 text-xs text-muted-foreground">
        {notes.length} documents
      </p>
    </div>
    <button
      class="rounded-md p-1.5 text-muted-foreground hover:bg-muted/60 hover:text-foreground"
      type="button"
      aria-label="Create Note"
      disabled={busy}
      onclick={beginCreate}
    >
      <Plus size={15} />
    </button>
  </div>

  {#if creating}
    <div class="mt-3 rounded-md border border-border bg-muted/20 p-2">
      <input
        bind:value={draftTitle}
        class="h-8 w-full rounded border border-border bg-background px-2 text-sm text-foreground outline-none focus:border-accent/45"
        placeholder="Note title"
        onkeydown={(event) => {
          if (event.key === 'Enter') confirmCreate();
          if (event.key === 'Escape') creating = false;
        }}
      />
      <div class="mt-2 flex items-center justify-end gap-1">
        <button
          class="rounded px-2 py-1 text-xs text-muted-foreground hover:bg-muted hover:text-foreground"
          type="button"
          onclick={() => (creating = false)}
        >
          Cancel
        </button>
        <button
          class="rounded bg-accent px-2 py-1 text-xs font-medium text-accent-foreground disabled:opacity-50"
          type="button"
          disabled={!draftTitle.trim() || busy}
          onclick={confirmCreate}
        >
          Create
        </button>
      </div>
    </div>
  {/if}

  <div class="mt-3 space-y-1">
    {#each notes as note}
      <div
        class={activeNoteId === note.id
          ? 'rounded-md border border-entity-note/35 bg-entity-note/10'
          : 'rounded-md border border-transparent hover:bg-muted/35'}
      >
        {#if editingNoteId === note.id}
          <div class="p-2">
            <input
              bind:value={editingTitle}
              class="h-8 w-full rounded border border-border bg-background px-2 text-sm text-foreground outline-none focus:border-accent/45"
              onkeydown={(event) => {
                if (event.key === 'Enter') confirmRename();
                if (event.key === 'Escape') editingNoteId = null;
              }}
            />
            <div class="mt-2 flex justify-end gap-1">
              <button
                class="rounded px-2 py-1 text-xs text-muted-foreground hover:bg-muted hover:text-foreground"
                type="button"
                onclick={() => (editingNoteId = null)}
              >
                Cancel
              </button>
              <button
                class="rounded bg-accent px-2 py-1 text-xs font-medium text-accent-foreground disabled:opacity-50"
                type="button"
                aria-label="Confirm Rename"
                disabled={!editingTitle.trim() || busy}
                onclick={confirmRename}
              >
                Rename
              </button>
            </div>
          </div>
        {:else}
          <button
            class="flex w-full items-start gap-2 px-2 py-2 text-left"
            type="button"
            disabled={busy}
            onclick={() => onSelect(note.id)}
          >
            <FileText
              size={14}
              class={activeNoteId === note.id
                ? 'mt-0.5 text-entity-note'
                : 'mt-0.5 text-muted-foreground'}
            />
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm text-foreground"
                >{note.title}</span
              >
              {#if note.is_primary}
                <span
                  class="mt-0.5 block text-[0.68rem] uppercase text-muted-foreground"
                >
                  Primary
                </span>
              {/if}
            </span>
          </button>
          <div class="flex items-center justify-end gap-0.5 px-1 pb-1">
            <button
              class="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-35"
              type="button"
              aria-label="Rename"
              disabled={note.is_primary || busy}
              onclick={() => beginRename(note)}
            >
              <Pencil size={13} />
            </button>
            <button
              class="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-35"
              type="button"
              aria-label="Duplicate"
              disabled={busy}
              onclick={() => onDuplicate(note.id)}
            >
              <Copy size={13} />
            </button>
            <button
              class="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-35"
              type="button"
              aria-label="Delete"
              disabled={note.is_primary || busy}
              onclick={() => onDelete(note.id)}
            >
              <Trash2 size={13} />
            </button>
          </div>
        {/if}
      </div>
    {/each}
  </div>
</aside>
