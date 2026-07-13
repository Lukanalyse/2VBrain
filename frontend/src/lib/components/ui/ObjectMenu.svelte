<script lang="ts">
  import { Copy, MoreHorizontal, Pencil, Trash2 } from '@lucide/svelte';

  import ConfirmDialog from '$lib/components/ui/ConfirmDialog.svelte';
  import type { LinkableObject } from '$lib/features/linking/types/linking';
  import {
    deleteObject,
    duplicateObject,
    renameObject,
    updateWorkspaceCollection
  } from '$lib/features/workspace/services/workspaceApi';
  import type { CollectionStatus } from '$lib/features/workspace/services/workspaceApi';

  type Props = {
    objectId: string;
    title: string;
    onDeleted?: (objectId: string) => void;
    onRenamed?: (object: LinkableObject) => void;
    onDuplicated?: (object: LinkableObject) => void;
    onMoved?: (objectId: string, status: CollectionStatus) => void;
    size?: number;
  };

  let {
    objectId,
    title,
    onDeleted,
    onRenamed,
    onDuplicated,
    onMoved,
    size = 15
  }: Props = $props();

  let isPaper = $derived(objectId.startsWith('paper:'));

  let open = $state(false);
  let confirming = $state(false);
  let renameOpen = $state(false);
  let renameDraft = $state('');
  let busy = $state(false);
  let error = $state<string | null>(null);

  const moves: { status: CollectionStatus; label: string }[] = [
    { status: 'inbox', label: 'Inbox' },
    { status: 'workspace', label: 'Workspace' },
    { status: 'library', label: 'Library' }
  ];

  function toggle(event: MouseEvent): void {
    event.stopPropagation();
    open = !open;
  }

  function startRename(event: MouseEvent): void {
    event.stopPropagation();
    open = false;
    renameDraft = title;
    error = null;
    renameOpen = true;
  }

  async function submitRename(): Promise<void> {
    const next = renameDraft.trim();
    if (!next || next === title) {
      renameOpen = false;
      return;
    }
    busy = true;
    error = null;
    try {
      const { object } = await renameObject(objectId, next);
      renameOpen = false;
      onRenamed?.(object);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Rename failed.';
    } finally {
      busy = false;
    }
  }

  async function runDuplicate(event: MouseEvent): Promise<void> {
    event.stopPropagation();
    open = false;
    const { object } = await duplicateObject(objectId);
    onDuplicated?.(object);
  }

  async function runMove(event: MouseEvent, status: CollectionStatus): Promise<void> {
    event.stopPropagation();
    open = false;
    await updateWorkspaceCollection(objectId, status);
    onMoved?.(objectId, status);
  }

  async function confirmDelete(): Promise<void> {
    busy = true;
    error = null;
    try {
      await deleteObject(objectId);
      confirming = false;
      onDeleted?.(objectId);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Delete failed.';
    } finally {
      busy = false;
    }
  }

  function focusOnMount(node: HTMLInputElement): void {
    node.focus();
    node.select();
  }
</script>

<svelte:window onclick={() => (open = false)} />

<div class="relative shrink-0">
  <button
    type="button"
    class="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition hover:bg-muted/60 hover:text-foreground"
    aria-label="Object actions"
    onclick={toggle}
  >
    <MoreHorizontal {size} />
  </button>
  {#if open}
    <div
      class="absolute right-0 top-8 z-30 w-44 overflow-hidden rounded-md border border-border bg-background py-1 shadow-lg"
      role="menu"
    >
      <button
        type="button"
        role="menuitem"
        class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm text-foreground transition hover:bg-muted/50"
        onclick={startRename}
      >
        <Pencil size={14} class="text-muted-foreground" />
        Rename
      </button>

      {#if !isPaper}
        <button
          type="button"
          role="menuitem"
          class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm text-foreground transition hover:bg-muted/50"
          onclick={runDuplicate}
        >
          <Copy size={14} class="text-muted-foreground" />
          Duplicate
        </button>
      {/if}

      {#if isPaper}
        <div class="my-1 border-t border-border/60"></div>
        <p class="px-3 py-1 text-[0.65rem] font-semibold uppercase tracking-wide text-muted-foreground">
          Move to
        </p>
        {#each moves as move}
          <button
            type="button"
            role="menuitem"
            class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm text-foreground transition hover:bg-muted/50"
            onclick={(event) => runMove(event, move.status)}
          >
            {move.label}
          </button>
        {/each}
      {/if}

      <div class="my-1 border-t border-border/60"></div>
      <button
        type="button"
        role="menuitem"
        class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm text-entity-review transition hover:bg-muted/50"
        onclick={(event) => {
          event.stopPropagation();
          open = false;
          confirming = true;
        }}
      >
        <Trash2 size={14} />
        Delete
      </button>
    </div>
  {/if}
</div>

{#if renameOpen}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <button
      type="button"
      class="absolute inset-0 bg-black/50"
      aria-label="Cancel"
      onclick={() => (renameOpen = false)}
    ></button>
    <div
      class="relative z-10 w-full max-w-sm rounded-lg border border-border bg-background p-5 shadow-xl"
      role="dialog"
      aria-modal="true"
    >
      <h2 class="text-base font-semibold text-foreground">Rename</h2>
      <input
        bind:value={renameDraft}
        class="ros-input mt-3"
        use:focusOnMount
        onkeydown={(event) => {
          if (event.key === 'Enter') submitRename();
          if (event.key === 'Escape') renameOpen = false;
        }}
      />
      {#if error}
        <p class="mt-2 text-xs text-entity-review">{error}</p>
      {/if}
      <div class="mt-4 flex justify-end gap-2">
        <button class="ros-btn-ghost" type="button" onclick={() => (renameOpen = false)}>
          Cancel
        </button>
        <button
          class="inline-flex h-8 items-center rounded-md bg-accent px-3 text-xs font-semibold text-accent-foreground transition hover:bg-accent/90 disabled:opacity-50"
          type="button"
          disabled={busy || !renameDraft.trim()}
          onclick={submitRename}
        >
          Save
        </button>
      </div>
    </div>
  </div>
{/if}

<ConfirmDialog
  open={confirming}
  title={`Delete "${title}"?`}
  message={error ??
    'This permanently removes the object, its notes and (for papers) its PDF from your vault. Existing links to it are kept but become empty.'}
  confirmLabel={busy ? 'Deleting…' : 'Delete'}
  {busy}
  onConfirm={confirmDelete}
  onCancel={() => {
    confirming = false;
    error = null;
  }}
/>
