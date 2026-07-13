<script lang="ts">
  import { page } from '$app/stores';
  import {
    Cpu,
    Eye,
    ExternalLink,
    Pencil,
    Search,
    X
  } from '@lucide/svelte';

  import NeuralCore from '$lib/components/NeuralCore.svelte';
  import { entityMeta, entityTypes } from '$lib/design/entities';
  import ObjectMenu from '$lib/components/ui/ObjectMenu.svelte';
  import TagBadges from '$lib/components/ui/TagBadges.svelte';
  import type {
    LinkableObject,
    LinkableType
  } from '$lib/features/linking/types/linking';
  import ProjectDashboard from '$lib/features/workspace/components/ProjectDashboard.svelte';
  import type { WorkspacePanelContext } from '$lib/features/workspace/types/panels';
  import {
    getExplorerDetail,
    searchExplorer
  } from '$lib/features/research-explorer/services/researchExplorerApi';
  import type { ExplorerObjectDetail } from '$lib/features/research-explorer/types/researchExplorer';
  import {
    getWorkspaceMarkdown,
    getWorkspacePdfUrl,
    getActiveWorkspace,
    saveWorkspaceMarkdown,
    updateWorkspaceStatus
  } from '$lib/features/workspace/services/workspaceApi';
  import type { ReadingStatus } from '$lib/features/workspace/services/workspaceApi';
  import MarkdownPreview from './MarkdownPreview.svelte';

  type Filter = 'all' | LinkableType;
  type SaveState = 'saved' | 'unsaved' | 'saving' | 'error';
  type ViewerTab = 'pdf' | 'notes';

  const filters: Filter[] = ['all', ...entityTypes];
  const readingStatuses: ReadingStatus[] = [
    'unread',
    'reading',
    'paused',
    'reviewed',
    'mastered'
  ];

  let query = $state('');
  let activeFilter = $state<Filter>('all');
  let items = $state<LinkableObject[]>([]);
  let listLoading = $state(true);
  let listError = $state<string | null>(null);

  let selected = $state<LinkableObject | null>(null);
  let detail = $state<ExplorerObjectDetail | null>(null);
  let content = $state('');
  let lastSaved = $state('');
  let saveState = $state<SaveState>('saved');
  let detailLoading = $state(false);
  let viewerTab = $state<ViewerTab>('pdf');
  let currentReadingStatus = $state<ReadingStatus>('unread');
  let showPreview = $state(false);
  let pdfMessage = $state<string | null>(null);
  let handledRequest = $state<string | null>(null);

  let searchTimer: ReturnType<typeof setTimeout> | null = null;
  let saveTimer: ReturnType<typeof setTimeout> | null = null;

  const isPaper = $derived(selected?.type === 'paper');
  const relatedItems = $derived(detail?.all_related ?? []);
  const requestedObjectId = $derived($page.url.searchParams.get('open'));
  const projectContext = $derived<WorkspacePanelContext | null>(
    selected && selected.type === 'project' && detail
      ? {
          object: selected,
          detail,
          content,
          saveState,
          updateContent,
          openObject,
          updateReadingStatus: async () => {},
          searchObjects: (value: string) => searchExplorer(value),
          appendReadingNote: (text: string) => {
            updateContent(content ? `${content}\n\n${text}` : text);
          },
          createConceptFromSelection: async () => {},
          createBrainstormFromSelection: async () => {},
          createProjectFromSelection: async () => {},
          createReviewFromSelection: async () => {},
          linkSelectionToConcept: async () => {},
          openPdf: async () => {},
          createConceptFromTitle: async () => null,
          createProjectFromTitle: async () => null,
          createReviewFromTitle: async () => null,
          createBrainstormFromTitle: async () => null,
          linkObjectToTarget: async () => {},
          refreshObject: async () => {
            if (selected) await openObject(selected);
          }
        }
      : null
  );

  // Reload the list whenever the query or the type filter changes (debounced).
  $effect(() => {
    const currentQuery = query;
    const currentFilter = activeFilter;
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      void loadList(currentQuery, currentFilter);
    }, 150);
    return () => {
      if (searchTimer) clearTimeout(searchTimer);
    };
  });

  $effect(() => {
    const objectId = requestedObjectId;
    if (!objectId || handledRequest === objectId) return;
    handledRequest = objectId;
    void openRequestedObject(objectId);
  });

  async function loadList(q: string, filter: Filter): Promise<void> {
    listLoading = true;
    listError = null;
    try {
      const workspace = await getActiveWorkspace();
      const seen = new Set<string>();
      const activeObjects = [
        ...workspace.projects,
        ...workspace.reading,
        ...workspace.writing,
        ...workspace.brainstorms
      ].filter((object) => {
        if (seen.has(object.id)) return false;
        seen.add(object.id);
        return true;
      });
      const normalizedQuery = q.trim().toLowerCase();
      items = activeObjects.filter(
        (object) =>
          (filter === 'all' || object.type === filter) &&
          (!normalizedQuery ||
            [object.title, object.subtitle]
              .filter(Boolean)
              .some((value) => value.toLowerCase().includes(normalizedQuery)))
      );
      if (!selected && !requestedObjectId && items[0]) {
        void openObject(items[0]);
      }
    } catch (error) {
      listError =
        error instanceof Error ? error.message : 'Unable to load active work.';
      items = [];
    } finally {
      listLoading = false;
    }
  }

  async function openRequestedObject(objectId: string): Promise<void> {
    try {
      const objectDetail = await getExplorerDetail(objectId);
      await openObject(objectDetail.object);
    } catch (error) {
      listError =
        error instanceof Error ? error.message : 'Unable to open this object.';
    }
  }

  async function openObject(object: LinkableObject): Promise<void> {
    if (selected?.id === object.id) return;
    await flushSave();
    selected = object;
    detail = null;
    detailLoading = true;
    pdfMessage = null;
    viewerTab = object.type === 'paper' ? 'pdf' : 'notes';
    showPreview = false;
    try {
      const [objectDetail, markdown] = await Promise.all([
        getExplorerDetail(object.id),
        getWorkspaceMarkdown(object.id)
      ]);
      detail = objectDetail;
      selected = objectDetail.object;
      content = markdown.content;
      currentReadingStatus = readingStatusFromMarkdown(markdown.content);
      lastSaved = markdown.content;
      saveState = 'saved';
    } catch (error) {
      listError =
        error instanceof Error ? error.message : 'Unable to open this object.';
    } finally {
      detailLoading = false;
    }
  }

  function updateContent(value: string): void {
    content = value;
    saveState = 'unsaved';
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(() => void saveNow(), 700);
  }

  async function saveNow(): Promise<void> {
    if (!selected || content === lastSaved) return;
    const target = selected.id;
    saveState = 'saving';
    try {
      const saved = await saveWorkspaceMarkdown(target, content);
      if (selected?.id !== target) return;
      lastSaved = saved.content;
      saveState = content === saved.content ? 'saved' : 'unsaved';
    } catch {
      saveState = 'error';
    }
  }

  async function flushSave(): Promise<void> {
    if (saveTimer) clearTimeout(saveTimer);
    await saveNow();
  }

  async function setStatus(status: ReadingStatus): Promise<void> {
    if (!selected || selected.type !== 'paper') return;
    try {
      const response = await updateWorkspaceStatus(selected.id, status);
      selected = response.object;
      currentReadingStatus = status;
    } catch {
      /* status is non-critical; ignore transient failures */
    }
  }

  function readingStatusFromMarkdown(markdown: string): ReadingStatus {
    const status = markdown.match(/^status:\s*["']?([^\n"']+)/m)?.[1]?.trim();
    return (readingStatuses as string[]).includes(status ?? '')
      ? (status as ReadingStatus)
      : 'unread';
  }

  function openPdfTab(): void {
    if (!selected) return;
    pdfMessage = null;
    const opened = window.open(getWorkspacePdfUrl(selected.id), '_blank', 'noopener');
    if (!opened) {
      pdfMessage =
        'Your browser blocked the PDF tab. Allow pop-ups for this site, then retry.';
    }
  }

  function clearSelection(): void {
    void flushSave();
    selected = null;
    detail = null;
    content = '';
    lastSaved = '';
  }

  function handleDeleted(objectId: string): void {
    items = items.filter((item) => item.id !== objectId);
    if (selected?.id === objectId) clearSelection();
    void loadList(query, activeFilter);
  }

  async function handleRenamed(object: LinkableObject): Promise<void> {
    selected = object;
    await openObject(object);
    void loadList(query, activeFilter);
  }

  function filterLabel(filter: Filter): string {
    return filter === 'all' ? 'All' : entityMeta[filter].plural;
  }

</script>

<section class="workspace-grid h-full overflow-hidden bg-background">
  <!-- LEFT: focused list of objects explicitly kept in active work -->
  <aside class="workspace-rail flex min-w-0 flex-col border-r border-border bg-background/88">
    <div class="relative border-b border-border p-4">
      <div class="flex items-center gap-3">
        <span class="rail-core" aria-hidden="true">
          <Cpu size={16} />
        </span>
        <span class="min-w-0">
          <span class="block text-[0.66rem] font-semibold uppercase text-accent">
            Workspace module
          </span>
          <span class="mt-0.5 block text-sm font-semibold text-foreground">
            Active desk
          </span>
        </span>
        <span class="rail-count">{items.length}</span>
      </div>
      <label
        class="mt-4 flex h-10 items-center gap-2 rounded-md border border-border bg-background/75 px-3 text-sm text-muted-foreground focus-within:border-accent/55"
      >
        <Search size={15} />
        <input
          bind:value={query}
          class="min-w-0 flex-1 bg-transparent text-foreground outline-none"
          placeholder="Filter active work..."
        />
        {#if query}
          <button
            type="button"
            class="rounded p-0.5 hover:bg-muted"
            aria-label="Clear search"
            onclick={() => (query = '')}
          >
            <X size={14} />
          </button>
        {/if}
      </label>

      <div class="mt-3 grid grid-cols-3 gap-1">
        {#each filters as filter}
          <button
            type="button"
            class={[
              'inline-flex h-7 min-w-0 items-center justify-center gap-1 rounded-md border px-1.5 text-[0.65rem] transition',
              activeFilter === filter
                ? 'border-accent/45 bg-accent/10 text-foreground'
                : 'border-border bg-muted/[0.08] text-muted-foreground hover:bg-muted/30 hover:text-foreground'
            ]}
            title={filterLabel(filter)}
            onclick={() => (activeFilter = filter)}
          >
            {#if filter !== 'all'}
              {@const Icon = entityMeta[filter].icon}
              <Icon size={12} class={entityMeta[filter].text} />
            {/if}
            <span class="truncate">{filterLabel(filter)}</span>
          </button>
        {/each}
      </div>
    </div>

    <div class="min-h-0 flex-1 overflow-y-auto p-2">
      {#if listLoading}
        <p class="px-2 py-3 text-sm text-muted-foreground">Loading...</p>
      {:else if listError}
        <p class="px-2 py-3 text-sm text-muted-foreground">{listError}</p>
      {:else if items.length === 0}
        <p class="px-2 py-3 text-sm text-muted-foreground">
          Your desk is clear. Move a source or idea here from the Library.
        </p>
      {:else}
        <ul class="workspace-thread-list">
          {#each items as item (item.id)}
            {@const Icon = entityMeta[item.type].icon}
            <li class="workspace-thread-slot">
              <button
                type="button"
                class={[
                  'workspace-thread flex w-full items-start gap-2.5 px-3 py-2.5 text-left transition',
                  selected?.id === item.id
                    ? 'workspace-thread--active text-foreground'
                    : 'text-muted-foreground hover:bg-muted/20 hover:text-foreground'
                ]}
                onclick={() => openObject(item)}
              >
                <span class={`thread-icon ${entityMeta[item.type].text}`}>
                  <Icon size={14} />
                </span>
                <span class="min-w-0 flex-1">
                  <span class="block truncate text-sm font-medium">{item.title}</span>
                  <span class="mt-0.5 block truncate text-[0.66rem] text-muted-foreground">
                    {entityMeta[item.type].label}{item.subtitle
                      ? ` · ${item.subtitle}`
                      : ''}
                  </span>
                </span>
                <span class="thread-port" aria-hidden="true"></span>
              </button>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  </aside>

  <!-- RIGHT: adaptive viewer -->
  <main class="workspace-viewer flex min-w-0 flex-col overflow-hidden">
    {#if !selected}
      <div class="flex flex-1 items-center justify-center p-6">
        <div class="flex max-w-sm flex-col items-center text-center">
          <NeuralCore compact label="Workspace Core" detail="Awaiting active thread" />
          <h2 class="-mt-4 text-lg font-semibold text-foreground">
            Select an active thread
          </h2>
          <p class="mt-2 text-sm leading-6 text-muted-foreground">
            Reading and writing happen here. The complete index stays in Library.
          </p>
        </div>
      </div>
    {:else}
      {@const Icon = entityMeta[selected.type].icon}
      <header class="workspace-document-header flex items-center gap-3 border-b border-border px-5 py-3">
        <span class={`document-node ${entityMeta[selected.type].text}`}>
          <Icon size={17} />
        </span>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <span
              class={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium ${entityMeta[selected.type].badge}`}
            >
              {entityMeta[selected.type].label}
            </span>
            <span class="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
              <span
                class={saveState === 'error'
                  ? 'h-1.5 w-1.5 bg-entity-review'
                  : saveState === 'unsaved'
                    ? 'h-1.5 w-1.5 bg-entity-brainstorm'
                    : 'h-1.5 w-1.5 bg-accent'}
              ></span>
              {saveState === 'saving'
                ? 'Saving...'
                : saveState === 'unsaved'
                  ? 'Unsaved'
                  : saveState === 'error'
                    ? 'Save failed'
                    : 'Saved'}
            </span>
          </div>
          <h1 class="mt-1 truncate text-lg font-semibold text-foreground">
            {selected.title}
          </h1>
        </div>

        <div class="flex shrink-0 items-center gap-2">
          {#if isPaper}
            <select
              class="h-8 rounded-md border border-border bg-muted/20 px-2 text-xs text-muted-foreground outline-none"
              value={currentReadingStatus}
              onchange={(event) =>
                setStatus(event.currentTarget.value as ReadingStatus)}
            >
              {#each readingStatuses as status}
                <option value={status}>{status}</option>
              {/each}
            </select>
          {/if}
          <button
            type="button"
            class="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-muted/20 px-2.5 text-xs text-muted-foreground transition hover:text-foreground"
            onclick={openPdfTab}
            class:hidden={!isPaper}
          >
            <ExternalLink size={13} /> Open PDF
          </button>
          <ObjectMenu
            objectId={selected.id}
            title={selected.title}
            onDeleted={handleDeleted}
            onRenamed={handleRenamed}
            onDuplicated={(object) => openObject(object)}
            onMoved={() => loadList(query, activeFilter)}
          />
        </div>
      </header>

      {#if isPaper}
        <div class="flex items-center gap-1 border-b border-border bg-muted/[0.05] px-3 py-1.5">
          <button
            type="button"
            class={[
              'rounded-md px-3 py-1 text-sm transition',
              viewerTab === 'pdf'
                ? 'bg-accent/10 text-foreground'
                : 'text-muted-foreground hover:text-foreground'
            ]}
            onclick={() => (viewerTab = 'pdf')}
          >
            PDF
          </button>
          <button
            type="button"
            class={[
              'rounded-md px-3 py-1 text-sm transition',
              viewerTab === 'notes'
                ? 'bg-accent/10 text-foreground'
                : 'text-muted-foreground hover:text-foreground'
            ]}
            onclick={() => (viewerTab = 'notes')}
          >
            Notes
          </button>
        </div>
      {/if}

      {#if pdfMessage}
        <div class="border-b border-border bg-muted/[0.08] px-5 py-2 text-xs text-muted-foreground">
          {pdfMessage}
        </div>
      {/if}

      <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
        {#if detailLoading}
          <p class="p-5 text-sm text-muted-foreground">Loading...</p>
        {:else if isPaper && viewerTab === 'pdf'}
          <iframe
            title={selected.title}
            src={getWorkspacePdfUrl(selected.id)}
            class="min-h-0 flex-1 border-0 bg-muted/10"
          ></iframe>
        {:else if projectContext}
          <ProjectDashboard context={projectContext} />
        {:else}
          <!-- Markdown editor / preview (notes, ideas, projects, concepts) -->
          <div class="flex items-center justify-between border-b border-border bg-muted/[0.04] px-5 py-1.5">
            <span class="inline-flex items-center gap-2 text-xs text-muted-foreground">
              <Cpu size={12} class="text-accent" />
              Writing surface
            </span>
            <button
              type="button"
              class="inline-flex items-center gap-1.5 rounded-md border border-border bg-muted/20 px-2.5 py-1 text-xs text-muted-foreground transition hover:text-foreground"
              onclick={() => (showPreview = !showPreview)}
            >
              {#if showPreview}
                <Pencil size={13} /> Edit
              {:else}
                <Eye size={13} /> Preview
              {/if}
            </button>
          </div>
          {#if showPreview}
            <div class="min-h-0 flex-1 overflow-y-auto">
              <MarkdownPreview
                content={content}
                objectTitle={selected.title}
                compact
                showMetadata={false}
              />
            </div>
          {:else}
            <textarea
              value={content}
              oninput={(event) => updateContent(event.currentTarget.value)}
              spellcheck="false"
              placeholder="Write here..."
              class="workspace-editor min-h-0 flex-1 resize-none bg-transparent px-6 py-5 font-mono text-sm leading-6 text-foreground outline-none"
            ></textarea>
          {/if}
        {/if}

        {#if detail && (relatedItems.length || (detail.tags?.length ?? 0))}
          <footer class="border-t border-border px-5 py-3">
            <TagBadges tags={detail.tags} />
            {#if relatedItems.length}
              <div class="mt-2 flex flex-wrap items-center gap-1.5">
                <span class="text-xs text-muted-foreground">Related:</span>
                {#each relatedItems.slice(0, 8) as related (related.id)}
                  {@const RelIcon = entityMeta[related.type].icon}
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 rounded-md border border-border bg-muted/15 px-2 py-0.5 text-xs text-muted-foreground transition hover:text-foreground"
                    onclick={() => openObject(related)}
                  >
                    <RelIcon size={11} class={entityMeta[related.type].text} />
                    <span class="max-w-40 truncate">{related.title}</span>
                  </button>
                {/each}
              </div>
            {/if}
          </footer>
        {/if}
      </div>
    {/if}
  </main>
</section>

<style>
  .workspace-grid {
    position: relative;
    display: grid;
    grid-template-columns: clamp(260px, 26vw, 360px) minmax(0, 1fr);
    background-image:
      linear-gradient(hsl(var(--foreground) / 0.025) 1px, transparent 1px),
      linear-gradient(90deg, hsl(var(--foreground) / 0.025) 1px, transparent 1px);
    background-size: 32px 32px;
  }

  .workspace-rail,
  .workspace-viewer {
    position: relative;
    z-index: 1;
  }

  .workspace-rail::after {
    content: '';
    position: absolute;
    right: -1px;
    top: 86px;
    width: 1px;
    height: 96px;
    background: hsl(var(--accent) / 0.5);
    box-shadow: 0 0 10px hsl(var(--accent) / 0.24);
  }

  .rail-core,
  .document-node,
  .thread-icon {
    display: inline-flex;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    border: 1px solid hsl(var(--border));
    border-radius: 7px;
    background: hsl(var(--muted) / 0.2);
  }

  .rail-core {
    width: 34px;
    height: 34px;
    border-color: hsl(var(--accent) / 0.4);
    color: hsl(var(--accent));
    box-shadow: inset 0 0 14px hsl(var(--accent) / 0.07);
  }

  .rail-count {
    display: inline-flex;
    min-width: 30px;
    height: 26px;
    margin-left: auto;
    align-items: center;
    justify-content: center;
    border-left: 1px solid hsl(var(--border));
    color: hsl(var(--foreground));
    font-size: 0.72rem;
    font-weight: 700;
  }

  .workspace-thread-list {
    position: relative;
  }

  .workspace-thread-list::before {
    content: '';
    position: absolute;
    bottom: 12px;
    left: 18px;
    top: 12px;
    width: 1px;
    background: hsl(var(--border));
  }

  .workspace-thread-slot {
    position: relative;
  }

  .workspace-thread {
    position: relative;
    border-block: 1px solid transparent;
  }

  .workspace-thread--active {
    border-color: hsl(var(--accent) / 0.35);
    background: hsl(var(--accent) / 0.075);
  }

  .thread-icon {
    position: relative;
    z-index: 1;
    width: 28px;
    height: 28px;
    background: hsl(var(--background));
  }

  .thread-port {
    width: 6px;
    height: 6px;
    margin-top: 11px;
    border: 1px solid hsl(var(--accent) / 0.5);
    background: hsl(var(--background));
  }

  .workspace-thread--active .thread-port {
    background: hsl(var(--accent));
    box-shadow: 0 0 8px hsl(var(--accent) / 0.55);
  }

  .workspace-viewer {
    background: hsl(var(--background) / 0.93);
  }

  .workspace-document-header {
    position: relative;
    background: hsl(var(--background) / 0.96);
  }

  .workspace-document-header::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    width: 23%;
    height: 1px;
    background: hsl(var(--accent) / 0.65);
  }

  .document-node {
    width: 36px;
    height: 36px;
  }

  .workspace-editor {
    background-image:
      linear-gradient(90deg, hsl(var(--accent) / 0.05) 1px, transparent 1px),
      linear-gradient(hsl(var(--foreground) / 0.018) 1px, transparent 1px);
    background-size: 40px 100%, 100% 28px;
  }

  @media (max-width: 820px) {
    .workspace-grid {
      grid-template-columns: minmax(0, 1fr);
      grid-template-rows: minmax(0, 40vh) minmax(0, 1fr);
    }

    .workspace-grid > aside {
      border-right: 0;
      border-bottom: 1px solid hsl(var(--border));
    }
  }
</style>
