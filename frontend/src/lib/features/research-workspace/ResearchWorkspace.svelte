<script lang="ts">
  import { page } from '$app/stores';
  import {
    ArrowLeft,
    Cpu,
    Eye,
    ExternalLink,
    GripVertical,
    Pencil,
    Plus,
    Quote,
    Search,
    X
  } from '@lucide/svelte';

  import NeuralCore from '$lib/components/NeuralCore.svelte';
  import { entityMeta, entityTypes } from '$lib/design/entities';
  import ObjectMenu from '$lib/components/ui/ObjectMenu.svelte';
  import TagBadges from '$lib/components/ui/TagBadges.svelte';
  import { assistantProjectUrl } from '$lib/features/assistant/services/assistantNavigation';
  import {
    readCitationFocus,
    type AssistantCitationFocus
  } from '$lib/features/assistant/services/assistantSession';
  import type {
    LinkableObject,
    LinkableType
  } from '$lib/features/linking/types/linking';
  import { createLinks } from '$lib/features/linking/services/linkingApi';
  import ProjectDashboard from '$lib/features/workspace/components/ProjectDashboard.svelte';
  import MarkdownPanel from '$lib/features/workspace/panels/MarkdownPanel.svelte';
  import type { WorkspacePanelContext } from '$lib/features/workspace/types/panels';
  import { createConcept } from '$lib/features/concepts/services/conceptsApi';
  import {
    getExplorerDetail,
    searchExplorer
  } from '$lib/features/research-explorer/services/researchExplorerApi';
  import type { ExplorerObjectDetail } from '$lib/features/research-explorer/types/researchExplorer';
  import {
    getWorkspaceMarkdown,
    getWorkspacePdfUrl,
    getActiveWorkspace,
    createBrainstorm,
    createProject,
    createWorkspaceNote,
    saveWorkspaceMarkdown,
    updateWorkspaceStatus
  } from '$lib/features/workspace/services/workspaceApi';
  import type { ReadingStatus } from '$lib/features/workspace/services/workspaceApi';
  import MarkdownPreview from './MarkdownPreview.svelte';

  type Filter = 'all' | LinkableType;
  type SaveState = 'saved' | 'unsaved' | 'saving' | 'error';
  type ViewerTab = 'pdf' | 'notes';
  type CreateKind = 'note' | 'brainstorm' | 'concept' | 'project';

  const filters: Filter[] = ['all', ...entityTypes];
  const createKinds: CreateKind[] = [
    'note',
    'brainstorm',
    'concept',
    'project'
  ];
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
  let activeObjects = $state<LinkableObject[]>([]);
  let activeObjectsLoaded = $state(false);
  let listLoading = $state(true);
  let listError = $state<string | null>(null);

  let selected = $state<LinkableObject | null>(null);
  let detail = $state<ExplorerObjectDetail | null>(null);
  let content = $state('');
  let documentPrefix = $state('');
  let lastSaved = $state('');
  let saveState = $state<SaveState>('saved');
  let detailLoading = $state(false);
  let viewerTab = $state<ViewerTab>('pdf');
  let currentReadingStatus = $state<ReadingStatus>('unread');
  let showPreview = $state(false);
  let pdfMessage = $state<string | null>(null);
  let handledRequest = $state<string | null>(null);
  let citationFocus = $state<AssistantCitationFocus | null>(null);
  let showCreate = $state(false);
  let createKind = $state<CreateKind>('note');
  let createTitle = $state('');
  let createBusy = $state(false);
  let createError = $state<string | null>(null);
  let focusEditorAfterOpen = $state(false);
  let createInput = $state<HTMLInputElement>();

  let searchTimer: ReturnType<typeof setTimeout> | null = null;
  let saveTimer: ReturnType<typeof setTimeout> | null = null;
  let saveTask: Promise<void> | null = null;
  let saveRequested = false;
  let openController: AbortController | null = null;
  let listRequest = 0;

  const isPaper = $derived(selected?.type === 'paper');
  const relatedItems = $derived(detail?.all_related ?? []);
  const requestedObjectId = $derived($page.url.searchParams.get('open'));
  const requestedCitationId = $derived($page.url.searchParams.get('citation'));
  const requestedAssistantProject = $derived(
    $page.url.searchParams.get('assistantProject')
  );
  const requestedSourceKind = $derived(
    sourceKindFromQuery($page.url.searchParams.get('sourceKind'))
  );
  const requestedPage = $derived(
    pageFromQuery($page.url.searchParams.get('page'))
  );
  const requestedObjectKey = $derived(
    requestedObjectId
      ? [
          requestedObjectId,
          requestedCitationId ?? '',
          requestedSourceKind ?? '',
          requestedPage ?? ''
        ].join('|')
      : null
  );
  const assistantReturnUrl = $derived(
    requestedAssistantProject
      ? assistantProjectUrl(requestedAssistantProject)
      : '/assistant'
  );
  const focusedCitation = $derived(
    citationFocus?.citation.object.id === selected?.id
      ? (citationFocus?.citation ?? null)
      : null
  );
  const focusedPdfPage = $derived(
    selected?.id === requestedObjectId && requestedSourceKind === 'pdf'
      ? (focusedCitation?.page_number ?? requestedPage)
      : null
  );
  const selectedPdfUrl = $derived(
    selected ? getWorkspacePdfUrl(selected.id, focusedPdfPage) : ''
  );
  const wordCount = $derived(
    content.trim() ? content.trim().split(/\s+/).length : 0
  );
  const noteContextTitle = $derived(
    selected?.type === 'note' ? selected.subtitle : selected?.title
  );
  const panelContext = $derived<WorkspacePanelContext | null>(
    selected && detail
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
            if (!selected) return;
            await openObject(selected, false, true);
            await loadList(query, activeFilter, true);
          }
        }
      : null
  );
  const projectContext = $derived(
    selected?.type === 'project' ? panelContext : null
  );
  const editorContext = $derived(
    selected?.type !== 'project' ? panelContext : null
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
    const focusId = requestedCitationId;
    citationFocus = focusId ? readCitationFocus(focusId) : null;
  });

  $effect(() => {
    const objectId = requestedObjectId;
    const requestKey = requestedObjectKey;
    const sourceKind = requestedSourceKind;
    if (!objectId || !requestKey || handledRequest === requestKey) return;
    handledRequest = requestKey;
    void openRequestedObject(objectId, sourceKind);
  });

  async function loadList(
    q: string,
    filter: Filter,
    refresh = false
  ): Promise<void> {
    const request = ++listRequest;
    const shouldFetch = refresh || !activeObjectsLoaded;
    if (shouldFetch) listLoading = true;
    listError = null;
    try {
      if (shouldFetch) {
        const workspace = await getActiveWorkspace(refresh);
        const seen = new Set<string>();
        activeObjects = [
          ...workspace.projects,
          ...workspace.reading,
          ...workspace.writing,
          ...workspace.brainstorms
        ].filter((object) => {
          if (seen.has(object.id)) return false;
          seen.add(object.id);
          return true;
        });
        activeObjectsLoaded = true;
      }
      const normalizedQuery = q.trim().toLowerCase();
      if (request !== listRequest) return;
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
      if (shouldFetch) listLoading = false;
    }
  }

  async function openRequestedObject(
    objectId: string,
    sourceKind: 'pdf' | 'markdown' | null
  ): Promise<void> {
    try {
      const objectDetail = await getExplorerDetail(objectId);
      await openObject(objectDetail.object);
      if (sourceKind === 'markdown') {
        viewerTab = 'notes';
        showPreview = true;
      } else if (sourceKind === 'pdf') {
        viewerTab = 'pdf';
      }
    } catch (error) {
      listError =
        error instanceof Error ? error.message : 'Unable to open this object.';
    }
  }

  async function openObject(
    object: LinkableObject,
    focusEditor = false,
    force = false
  ): Promise<void> {
    if (selected?.id === object.id && !force) return;
    if (!(await flushSave())) return;
    openController?.abort();
    const controller = new AbortController();
    openController = controller;
    selected = object;
    focusEditorAfterOpen = focusEditor;
    detail = null;
    detailLoading = true;
    pdfMessage = null;
    viewerTab = object.type === 'paper' ? 'pdf' : 'notes';
    showPreview = false;
    try {
      const [objectDetail, markdown] = await Promise.all([
        getExplorerDetail(object.id, controller.signal),
        getWorkspaceMarkdown(object.id, controller.signal)
      ]);
      if (openController !== controller) return;
      detail = objectDetail;
      selected = objectDetail.object;
      currentReadingStatus = readingStatusFromMarkdown(markdown.content);
      const editable = splitMarkdownDocument(markdown.content);
      documentPrefix = editable.prefix;
      content = editable.body;
      lastSaved = editable.body;
      saveState = 'saved';
    } catch (error) {
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        listError =
          error instanceof Error ? error.message : 'Unable to open this object.';
      }
    } finally {
      if (openController === controller) detailLoading = false;
    }
  }

  function updateContent(value: string): void {
    content = value;
    saveState = 'unsaved';
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(() => void saveNow(), 700);
  }

  async function saveNow(): Promise<void> {
    saveRequested = true;
    if (saveTask) return saveTask;
    saveTask = drainSaves().finally(() => {
      saveTask = null;
    });
    return saveTask;
  }

  async function drainSaves(): Promise<void> {
    while (saveRequested) {
      saveRequested = false;
      if (!selected || content === lastSaved) continue;
      const target = selected.id;
      const snapshot = content;
      const prefix = documentPrefix;
      saveState = 'saving';
      try {
        const saved = await saveWorkspaceMarkdown(
          target,
          `${prefix}${snapshot}`
        );
        if (selected?.id !== target) continue;
        const editable = splitMarkdownDocument(saved.content);
        documentPrefix = editable.prefix;
        lastSaved = editable.body;
        saveState = content === editable.body ? 'saved' : 'unsaved';
      } catch {
        saveState = 'error';
        saveRequested = false;
        break;
      }
    }
  }

  async function flushSave(): Promise<boolean> {
    if (saveTimer) clearTimeout(saveTimer);
    await saveNow();
    return saveState !== 'error';
  }

  function retrySave(): void {
    saveState = 'unsaved';
    void saveNow();
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

  function sourceKindFromQuery(
    value: string | null
  ): 'pdf' | 'markdown' | null {
    return value === 'pdf' || value === 'markdown' ? value : null;
  }

  function pageFromQuery(value: string | null): number | null {
    if (!value) return null;
    const parsed = Number.parseInt(value, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
  }

  function openPdfTab(): void {
    if (!selected) return;
    pdfMessage = null;
    const opened = window.open(
      getWorkspacePdfUrl(selected.id),
      '_blank',
      'noopener'
    );
    if (!opened) {
      pdfMessage =
        'Your browser blocked the PDF tab. Allow pop-ups for this site, then retry.';
    }
  }

  function clearSelection(): void {
    void flushSave();
    openController?.abort();
    selected = null;
    detail = null;
    content = '';
    documentPrefix = '';
    lastSaved = '';
  }

  function handleDeleted(objectId: string): void {
    items = items.filter((item) => item.id !== objectId);
    if (selected?.id === objectId) clearSelection();
    void loadList(query, activeFilter, true);
  }

  async function handleRenamed(object: LinkableObject): Promise<void> {
    selected = object;
    await openObject(object, false, true);
    void loadList(query, activeFilter, true);
  }

  function filterLabel(filter: Filter): string {
    return filter === 'all' ? 'All' : entityMeta[filter].plural;
  }

  function splitMarkdownDocument(markdown: string): {
    prefix: string;
    body: string;
  } {
    const frontmatter = markdown.match(/^---\r?\n[\s\S]*?\r?\n---\r?\n*/);
    if (!frontmatter) return { prefix: '', body: markdown };
    return {
      prefix: frontmatter[0],
      body: markdown.slice(frontmatter[0].length)
    };
  }

  function markdownStem(path: string): string {
    return (path.split(/[\\/]/).pop() ?? path).replace(/\.md$/i, '');
  }

  function startObjectDrag(event: DragEvent, object: LinkableObject): void {
    if (selected?.type !== 'project' || object.id === selected.id) {
      event.preventDefault();
      return;
    }
    event.dataTransfer?.setData(
      'application/x-research-object',
      JSON.stringify(object)
    );
    event.dataTransfer?.setData('text/plain', object.id);
    if (event.dataTransfer) event.dataTransfer.effectAllowed = 'copy';
  }

  function openCreate(
    kind: CreateKind = selected ? 'note' : 'brainstorm'
  ): void {
    showCreate = true;
    createKind = kind;
    createTitle = '';
    createError = null;
    requestAnimationFrame(() => createInput?.focus());
  }

  function closeCreate(): void {
    showCreate = false;
    createTitle = '';
    createError = null;
  }

  function selectCreateKind(kind: CreateKind): void {
    if (kind === 'note' && !selected) return;
    createKind = kind;
    createError = null;
    requestAnimationFrame(() => createInput?.focus());
  }

  async function resolveNoteParent(): Promise<LinkableObject | null> {
    if (!selected) return null;
    if (selected.type !== 'note') return selected;
    const parentTitle = selected.subtitle;
    const candidates = await searchExplorer(parentTitle);
    return (
      candidates.find(
        (item) => item.type !== 'note' && item.title === parentTitle
      ) ?? null
    );
  }

  async function createWriting(): Promise<void> {
    const title = createTitle.trim();
    if (!title || createBusy) return;
    createBusy = true;
    createError = null;

    try {
      let createdObject: LinkableObject;
      if (createKind === 'note') {
        const parent = await resolveNoteParent();
        if (!parent) throw new Error('Select a thread before creating a note.');
        const created = await createWorkspaceNote(parent.id, title);
        createdObject = {
          id: `note:${markdownStem(created.object.markdown_path)}::${created.note.id}`,
          type: 'note',
          title: created.note.title,
          subtitle: created.object.title,
          markdown_path: created.note.path
        };
        if (parent.type === 'project') {
          await createLinks(parent.id, [createdObject.id]);
        }
      } else if (createKind === 'brainstorm') {
        createdObject = (await createBrainstorm(title)).object;
      } else if (createKind === 'concept') {
        const created = await createConcept({
          name: title,
          description: '',
          category: 'Research',
          tags: []
        });
        createdObject = {
          id: `concept:${created.slug}`,
          type: 'concept',
          title: created.name,
          subtitle: created.category || 'Concept',
          markdown_path: created.markdown_path
        };
      } else {
        createdObject = (await createProject(title)).object;
      }

      query = '';
      activeFilter = 'all';
      closeCreate();
      await openObject(createdObject, createdObject.type !== 'project');
      await loadList('', 'all', true);
    } catch (error) {
      createError =
        error instanceof Error ? error.message : 'Unable to create this item.';
    } finally {
      createBusy = false;
    }
  }
</script>

<section class="workspace-grid h-full overflow-hidden bg-background">
  <!-- LEFT: focused list of objects explicitly kept in active work -->
  <aside
    class="workspace-rail flex min-w-0 flex-col border-r border-border/90 bg-surface/90"
  >
    <div class="relative border-b border-border p-4">
      <div class="flex items-center gap-3">
        <span class="rail-core" aria-hidden="true">
          <Cpu size={16} />
        </span>
        <span class="min-w-0">
          <span
            class="block text-[0.66rem] font-semibold uppercase text-accent"
          >
            Workspace module
          </span>
          <span class="mt-0.5 block text-sm font-semibold text-foreground">
            Active desk
          </span>
        </span>
        <span class="rail-count">{items.length}</span>
      </div>

      {#if showCreate}
        <div
          class="quick-create mt-3 border border-accent/35 bg-surface-raised/80 p-3 shadow-panel"
        >
          <div class="flex items-center justify-between gap-2">
            <span
              class="inline-flex items-center gap-2 text-xs font-semibold uppercase text-accent"
            >
              <Plus size={13} /> New writing
            </span>
            <button
              type="button"
              class="ros-btn-icon h-7 w-7"
              aria-label="Close new writing"
              onclick={closeCreate}
            >
              <X size={13} />
            </button>
          </div>

          <div class="mt-3 grid grid-cols-2 gap-1.5">
            {#each createKinds as kind}
              {@const CreateIcon = entityMeta[kind].icon}
              <button
                type="button"
                class={[
                  'flex h-8 min-w-0 items-center gap-2 rounded-md border px-2 text-xs transition',
                  createKind === kind
                    ? `${entityMeta[kind].border} ${entityMeta[kind].tint} text-foreground`
                    : 'border-border/80 bg-surface text-muted-foreground hover:text-foreground',
                  kind === 'note' && !selected
                    ? 'cursor-not-allowed opacity-40'
                    : ''
                ]}
                disabled={kind === 'note' && !selected}
                aria-pressed={createKind === kind}
                onclick={() => selectCreateKind(kind)}
              >
                <CreateIcon size={13} class={entityMeta[kind].text} />
                <span class="truncate">{entityMeta[kind].label}</span>
              </button>
            {/each}
          </div>

          {#if createKind === 'note' && noteContextTitle}
            <p class="mt-2 truncate text-[0.68rem] text-muted-foreground">
              Linked to <span class="text-foreground">{noteContextTitle}</span>
            </p>
          {/if}

          <div class="mt-2 flex gap-2">
            <input
              bind:this={createInput}
              bind:value={createTitle}
              class="ros-input min-w-0"
              placeholder={`${entityMeta[createKind].label} title`}
              onkeydown={(event) => {
                if (event.key === 'Enter') void createWriting();
                if (event.key === 'Escape') closeCreate();
              }}
            />
            <button
              type="button"
              class="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md bg-accent px-3 text-xs font-semibold text-accent-foreground disabled:opacity-45"
              disabled={!createTitle.trim() || createBusy}
              onclick={createWriting}
            >
              <Plus size={13} /> Create
            </button>
          </div>

          {#if createError}
            <p class="mt-2 text-xs text-entity-review">{createError}</p>
          {/if}
        </div>
      {:else}
        <button
          type="button"
          class="mt-3 flex h-10 w-full items-center justify-center gap-2 rounded-md border border-accent/45 bg-accent/10 text-sm font-semibold text-accent transition hover:border-accent/70 hover:bg-accent/15"
          onclick={() => openCreate()}
        >
          <Plus size={16} /> New writing
        </button>
      {/if}

      <label
        class="mt-3 flex h-10 items-center gap-2 rounded-md border border-border/90 bg-surface-raised/55 px-3 text-sm text-muted-foreground focus-within:border-accent/70 focus-within:ring-2 focus-within:ring-accent/10"
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
                : 'border-border/90 bg-surface-raised/45 text-muted-foreground hover:bg-muted/55 hover:text-foreground'
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
                draggable={selected?.type === 'project' &&
                  item.id !== selected.id}
                class={[
                  'workspace-thread flex w-full items-start gap-2.5 px-3 py-2.5 text-left transition',
                  selected?.type === 'project' && item.id !== selected.id
                    ? 'cursor-grab active:cursor-grabbing'
                    : '',
                  selected?.id === item.id
                    ? 'workspace-thread--active text-foreground'
                    : 'text-muted-foreground hover:bg-muted/40 hover:text-foreground'
                ]}
                onclick={() => openObject(item)}
                ondragstart={(event) => startObjectDrag(event, item)}
              >
                <span class={`thread-icon ${entityMeta[item.type].text}`}>
                  <Icon size={14} />
                </span>
                <span class="min-w-0 flex-1">
                  <span class="block truncate text-sm font-medium"
                    >{item.title}</span
                  >
                  <span
                    class="mt-0.5 block truncate text-[0.66rem] text-muted-foreground"
                  >
                    {entityMeta[item.type].label}{item.subtitle
                      ? ` · ${item.subtitle}`
                      : ''}
                  </span>
                </span>
                {#if selected?.type === 'project' && item.id !== selected.id}
                  <GripVertical
                    size={13}
                    class="mt-1 shrink-0 text-muted-foreground/55"
                    aria-label="Drag into project"
                  />
                {/if}
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
          <NeuralCore
            compact
            label="Workspace Core"
            detail="Awaiting active thread"
          />
          <h2 class="-mt-4 text-lg font-semibold text-foreground">
            Select an active thread
          </h2>
          <p class="mt-2 text-sm leading-6 text-muted-foreground">
            Reading and writing happen here. The complete index stays in
            Library.
          </p>
          <button
            type="button"
            class="mt-5 inline-flex h-10 items-center gap-2 rounded-md bg-accent px-4 text-sm font-semibold text-accent-foreground"
            onclick={() => openCreate('brainstorm')}
          >
            <Plus size={16} /> New writing
          </button>
        </div>
      </div>
    {:else}
      {@const Icon = entityMeta[selected.type].icon}
      <header
        class="workspace-document-header flex items-center gap-3 border-b border-border/90 bg-surface/60 px-5 py-3 shadow-panel"
      >
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
            <span
              class="inline-flex items-center gap-1.5 text-xs text-muted-foreground"
            >
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
            {#if saveState === 'error'}
              <button
                type="button"
                class="rounded-md border border-entity-review/35 px-2 py-0.5 text-[11px] text-entity-review transition hover:bg-entity-review/10"
                onclick={retrySave}
              >
                Retry
              </button>
            {/if}
          </div>
          <h1 class="mt-1 truncate text-lg font-semibold text-foreground">
            {selected.title}
          </h1>
        </div>

        <div class="flex shrink-0 items-center gap-2">
          <button
            type="button"
            class="inline-flex h-8 items-center gap-1.5 rounded-md border border-entity-note/35 bg-entity-note/[0.08] px-2.5 text-xs text-entity-note transition hover:bg-entity-note/15"
            aria-label="Create note for current thread"
            onclick={() => openCreate('note')}
          >
            <Plus size={13} /> <span class="hidden sm:inline">Note</span>
          </button>
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
            onMoved={() => loadList(query, activeFilter, true)}
          />
        </div>
      </header>

      {#if isPaper}
        <div
          class="flex items-center gap-1 border-b border-border/90 bg-surface/60 px-3 py-1.5"
        >
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

      {#if focusedCitation}
        <div
          class="border-b border-accent/25 bg-accent/[0.055] px-4 py-3"
          aria-label="Assistant cited passage"
        >
          <div class="flex flex-wrap items-start gap-3">
            <span
              class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-accent/35 bg-accent/10 text-accent"
            >
              <Quote size={14} />
            </span>
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
                <span
                  class="text-[0.68rem] font-semibold uppercase text-accent"
                >
                  Assistant source
                </span>
                <span class="text-xs text-muted-foreground">
                  {focusedCitation.source_title}
                  {#if focusedCitation.page_number}
                    · Page {focusedCitation.page_number}
                  {/if}
                  {#if focusedCitation.heading !== `Page ${focusedCitation.page_number}`}
                    · {focusedCitation.heading}
                  {/if}
                </span>
              </div>
              <p class="mt-1.5 text-sm leading-6 text-foreground/90">
                {focusedCitation.excerpt}
              </p>
            </div>
            <a
              href={assistantReturnUrl}
              class="inline-flex h-8 shrink-0 items-center gap-1.5 rounded-md border border-border bg-background px-2.5 text-xs font-medium text-muted-foreground transition hover:border-accent/40 hover:text-foreground"
            >
              <ArrowLeft size={13} /> Back to conversation
            </a>
          </div>
        </div>
      {/if}

      {#if pdfMessage}
        <div
          class="border-b border-border bg-muted/[0.08] px-5 py-2 text-xs text-muted-foreground"
        >
          {pdfMessage}
        </div>
      {/if}

      <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
        {#if detailLoading}
          <p class="p-5 text-sm text-muted-foreground">Loading...</p>
        {:else if isPaper && viewerTab === 'pdf'}
          {#key selectedPdfUrl}
            <iframe
              title={selected.title}
              src={selectedPdfUrl}
              class="min-h-0 flex-1 border-0 bg-muted/10"
            ></iframe>
          {/key}
        {:else if projectContext}
          <ProjectDashboard context={projectContext} />
        {:else if editorContext}
          <!-- Markdown editor / preview (notes, ideas, projects, concepts) -->
          <div
            class="flex items-center justify-between border-b border-border/90 bg-surface/50 px-5 py-1.5"
          >
            <span
              class="inline-flex min-w-0 items-center gap-3 text-xs text-muted-foreground"
            >
              <span class="inline-flex items-center gap-2">
                <Cpu size={12} class="text-accent" />
                Writing surface
              </span>
              <span class="h-3 w-px bg-border"></span>
              <span>{wordCount} {wordCount === 1 ? 'word' : 'words'}</span>
            </span>
            <div class="flex items-center gap-2">
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
          </div>
          {#if showPreview}
            <div class="min-h-0 flex-1 overflow-y-auto">
              <MarkdownPreview
                {content}
                objectTitle={selected.title}
                compact
                showMetadata={false}
              />
            </div>
          {:else}
            <div
              class="writing-stage min-h-0 flex-1 overflow-hidden p-3 sm:p-5"
            >
              <div
                class="mx-auto h-full max-w-5xl overflow-hidden border-x border-border/80 bg-surface/35 shadow-panel"
              >
                {#key selected.id}
                  <MarkdownPanel
                    context={editorContext}
                    autofocus={focusEditorAfterOpen}
                    placeholder={`Write in ${selected.title}...`}
                  />
                {/key}
              </div>
            </div>
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
    grid-template-rows: minmax(0, 1fr);
    background-image:
      linear-gradient(hsl(var(--foreground) / 0.04) 1px, transparent 1px),
      linear-gradient(90deg, hsl(var(--foreground) / 0.04) 1px, transparent 1px);
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
    background: hsl(var(--accent) / 0.11);
  }

  .thread-icon {
    position: relative;
    z-index: 1;
    width: 28px;
    height: 28px;
    background: hsl(var(--surface));
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

  .quick-create {
    border-radius: 7px;
    box-shadow:
      inset 0 1px 0 hsl(var(--foreground) / 0.04),
      0 12px 30px hsl(210 20% 2% / 0.2);
  }

  .writing-stage {
    background:
      linear-gradient(
        90deg,
        transparent 0,
        hsl(var(--accent) / 0.035) 50%,
        transparent 100%
      ),
      hsl(var(--background) / 0.88);
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
