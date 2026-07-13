<script lang="ts">
  import { onDestroy, onMount } from 'svelte';

  import Card from '$lib/components/ui/Card.svelte';
  import DocumentPanel from '$lib/features/knowledge/components/DocumentPanel.svelte';
  import KnowledgeSidebar from '$lib/features/knowledge/components/KnowledgeSidebar.svelte';
  import MetadataPanel from '$lib/features/knowledge/components/MetadataPanel.svelte';
  import NotesEditor from '$lib/features/knowledge/components/NotesEditor.svelte';
  import PlaceholderPanel from '$lib/features/knowledge/components/PlaceholderPanel.svelte';
  import LinkPicker from '$lib/features/linking/components/LinkPicker.svelte';
  import RelationsPanel from '$lib/features/linking/components/RelationsPanel.svelte';
  import {
    getKnowledgeItem,
    getMarkdownDocument,
    saveMarkdownDocument
  } from '$lib/features/knowledge/services/knowledgeApi';
  import { activeKnowledgeItem } from '$lib/features/knowledge/stores/knowledgeStore';
  import type {
    KnowledgeItem,
    KnowledgeTab,
    SaveState
  } from '$lib/features/knowledge/types/knowledge';

  export let itemId: number;

  let item: KnowledgeItem | null = null;
  let markdownContent = '';
  let lastSavedContent = '';
  let activeTab: KnowledgeTab = 'notes';
  let saveState: SaveState = 'saved';
  let isLoading = true;
  let errorMessage: string | null = null;
  let saveTimer: ReturnType<typeof setTimeout> | null = null;
  let hasLoadedMarkdown = false;
  let relationsPanel: RelationsPanel;

  const tabs: { id: KnowledgeTab; label: string }[] = [
    { id: 'notes', label: 'Notes' },
    { id: 'metadata', label: 'Metadata' },
    { id: 'concepts', label: 'Concepts' },
    { id: 'relations', label: 'Relations' },
    { id: 'references', label: 'References' },
    { id: 'ai', label: 'AI' }
  ];

  onMount(async () => {
    try {
      const [loadedItem, document] = await Promise.all([
        getKnowledgeItem(itemId),
        getMarkdownDocument(itemId)
      ]);
      item = loadedItem;
      activeKnowledgeItem.set(loadedItem);
      markdownContent = document.content;
      lastSavedContent = document.content;
      hasLoadedMarkdown = true;
    } catch (error) {
      errorMessage =
        error instanceof Error
          ? error.message
          : 'Unable to load Knowledge Workspace.';
    } finally {
      isLoading = false;
    }
  });

  onDestroy(() => {
    if (saveTimer) clearTimeout(saveTimer);
  });

  $: if (hasLoadedMarkdown && markdownContent !== lastSavedContent) {
    scheduleSave();
  }

  function scheduleSave(): void {
    saveState = 'unsaved';
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(saveCurrentMarkdown, 700);
  }

  async function saveCurrentMarkdown(): Promise<void> {
    if (!item || markdownContent === lastSavedContent) return;

    saveState = 'saving';
    try {
      const document = await saveMarkdownDocument(item.id, markdownContent);
      lastSavedContent = document.content;
      saveState = 'saved';
    } catch {
      saveState = 'error';
    }
  }
</script>

{#if isLoading}
  <section
    class="flex min-h-[calc(100vh-4rem)] items-center justify-center px-6"
  >
    <p class="text-sm text-muted-foreground">Loading Knowledge Workspace...</p>
  </section>
{:else if errorMessage || !item}
  <section
    class="flex min-h-[calc(100vh-4rem)] items-center justify-center px-6"
  >
    <Card className="max-w-md p-5 text-center">
      <h1 class="text-lg font-semibold text-foreground">
        Unable to open document
      </h1>
      <p class="mt-3 text-sm leading-6 text-muted-foreground">{errorMessage}</p>
    </Card>
  </section>
{:else}
  <section class="flex min-h-[calc(100vh-4rem)] flex-col lg:flex-row">
    <KnowledgeSidebar {item} />
    <DocumentPanel {item} />

    <main class="flex min-w-0 flex-1 flex-col bg-background">
      <div class="border-b border-border px-4 py-3 lg:px-5">
        <div class="flex gap-1 overflow-x-auto">
          {#each tabs as tab}
            <button
              class={[
                'h-9 shrink-0 rounded-md px-3 text-sm transition',
                activeTab === tab.id
                  ? 'bg-muted text-foreground'
                  : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
              ]}
              type="button"
              on:click={() => (activeTab = tab.id)}
            >
              {tab.label}
            </button>
          {/each}
        </div>
      </div>

      {#if activeTab === 'notes'}
        <NotesEditor bind:content={markdownContent} {saveState} />
      {:else if activeTab === 'metadata'}
        <MetadataPanel {item} />
      {:else if activeTab === 'concepts'}
        <section class="space-y-5 p-5">
          <LinkPicker
            sourceId={`paper:${item.id}`}
            allowedTypes={['concept']}
            on:linked={() => relationsPanel?.refresh()}
          />
        </section>
      {:else if activeTab === 'relations'}
        <section class="space-y-5 p-5">
          <LinkPicker
            sourceId={`paper:${item.id}`}
            on:linked={() => relationsPanel?.refresh()}
          />
          <RelationsPanel
            bind:this={relationsPanel}
            sourceId={`paper:${item.id}`}
          />
        </section>
      {:else if activeTab === 'references'}
        <PlaceholderPanel
          title="Coming Soon"
          message="References will be connected here."
        />
      {:else}
        <PlaceholderPanel
          title="Coming Soon"
          message="Connect a Local LLM or API provider to start exploring your knowledge base."
        />
      {/if}
    </main>
  </section>
{/if}
