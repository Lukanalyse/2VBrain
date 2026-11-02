<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import {
    ArrowLeft,
    Cpu,
    Eye,
    ExternalLink,
    GripVertical,
    Link2,
    Palette,
    Pencil,
    Plus,
    Quote,
    Search,
    X
  } from '@lucide/svelte';

  import NeuralCore from '$lib/components/NeuralCore.svelte';
  import { entityMeta } from '$lib/design/entities';
  import ObjectMenu from '$lib/components/ui/ObjectMenu.svelte';
  import TagBadges from '$lib/components/ui/TagBadges.svelte';
  import { assistantProjectUrl } from '$lib/features/assistant/services/assistantNavigation';
  import { deleteConnection } from '$lib/features/connections/services/connectionsApi';
  import {
    readCitationFocus,
    type AssistantCitationFocus
  } from '$lib/features/assistant/services/assistantSession';
  import type {
    LinkableObject,
    LinkableType
  } from '$lib/features/linking/types/linking';
  import { createLinks } from '$lib/features/linking/services/linkingApi';
  import LinkPicker from '$lib/features/linking/components/LinkPicker.svelte';
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
    createStandaloneNote,
    saveWorkspaceMarkdown,
    setObjectColor,
    updateWorkspaceStatus
  } from '$lib/features/workspace/services/workspaceApi';
  import type { ReadingStatus } from '$lib/features/workspace/services/workspaceApi';
  import MarkdownPreview from './MarkdownPreview.svelte';
  import PdfReader from './PdfReader.svelte';
  import { noteColors, noteColorHsl } from '$lib/design/noteColors';

  type Filter = 'all' | LinkableType;
  type SaveState = 'saved' | 'unsaved' | 'saving' | 'error';
  type ViewerTab = 'pdf' | 'notes' | 'split';
  type CreateKind = 'note' | 'brainstorm' | 'concept' | 'project';

  const filters: Filter[] = ['all', 'note', 'paper', 'project'];
  const createKinds: CreateKind[] = ['note', 'project'];
  const coreTypes = new Set<LinkableType>(['note', 'paper', 'project']);
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
  let splitRatio = $state(50);
  let splitView = $state<HTMLDivElement | null>(null);
  let resizingSplit = $state(false);
  let splitEditorObject = $state<LinkableObject | null>(null);
  let splitEditorContent = $state('');
  let splitEditorPrefix = $state('');
  let splitEditorLastSaved = $state('');
  let splitEditorSaveState = $state<SaveState>('saved');
  let splitEditorLoading = $state(false);
  let currentReadingStatus = $state<ReadingStatus>('unread');
  let showPreview = $state(false);
  let pdfMessage = $state<string | null>(null);
  let handledRequest = $state<string | null>(null);
  let handledCreateRequest = $state<string | null>(null);
  let citationFocus = $state<AssistantCitationFocus | null>(null);
  let showCreate = $state(false);
  let createKind = $state<CreateKind>('note');
  let createTitle = $state('');
  let createColor = $state('cyan');
  let createBusy = $state(false);
  let createError = $state<string | null>(null);
  let showConnections = $state(false);
  let showColorPicker = $state(false);
  let colorBusy = $state(false);
  let connectionBusy = $state<string | null>(null);
  let focusEditorAfterOpen = $state(false);
  let createInput = $state<HTMLInputElement>();

  let searchTimer: ReturnType<typeof setTimeout> | null = null;
  let saveTimer: ReturnType<typeof setTimeout> | null = null;
  let saveTask: Promise<void> | null = null;
  let saveRequested = false;
  let splitSaveTimer: ReturnType<typeof setTimeout> | null = null;
  let splitSaveTask: Promise<void> | null = null;
  let splitSaveRequested = false;
  let openController: AbortController | null = null;
  let listRequest = 0;

  const isPaper = $derived(selected?.type === 'paper');
  const relatedItems = $derived(detail?.all_related ?? []);
  const requestedObjectId = $derived($page.url.searchParams.get('open'));
  const requestedCreateKind = $derived(
    createKindFromQuery($page.url.searchParams.get('create'))
  );
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
  const noteContextTitle = $derived(selected?.title);
  const connectionTypes = $derived<LinkableType[]>(
    selected?.type === 'note'
      ? ['paper', 'project', 'note']
      : selected?.type === 'paper'
        ? ['project', 'note']
        : ['paper', 'note']
  );
  const connectedIds = $derived(relatedItems.map((item) => item.id));
  const connectedNotes = $derived(
    relatedItems.filter((item) => item.type === 'note')
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
  const splitEditorContext = $derived<WorkspacePanelContext | null>(
    splitEditorObject
      ? {
          object: splitEditorObject,
          detail: null,
          content: splitEditorContent,
          saveState: splitEditorSaveState,
          updateContent: updateSplitContent,
          openObject,
          updateReadingStatus: async () => {},
          searchObjects: (value: string) => searchExplorer(value),
          appendReadingNote: (text: string) => {
            updateSplitContent(
              splitEditorContent ? `${splitEditorContent}\n\n${text}` : text
            );
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
            if (splitEditorObject) {
              await selectSplitEditor(splitEditorObject.id, true);
            }
          }
        }
      : null
  );
  const activeSplitContext = $derived(splitEditorContext ?? editorContext);

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

  $effect(() => {
    const kind = requestedCreateKind;
    if (!kind) {
      handledCreateRequest = null;
      return;
    }
    const contextId = selected?.id ?? requestedObjectId ?? '';
    if (kind === 'note' && !selected) return;
    const requestKey = `${kind}|${contextId}`;
    if (handledCreateRequest === requestKey) return;
    handledCreateRequest = requestKey;
    openCreate(kind);

    const url = new URL($page.url);
    url.searchParams.delete('create');
    void goto(`${url.pathname}${url.search}${url.hash}`, {
      replaceState: true,
      keepFocus: true,
      noScroll: true
    });
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
          if (!coreTypes.has(object.type)) return false;
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
    if (!(await flushSplitSave())) return;
    if (!(await flushSave())) return;
    openController?.abort();
    const controller = new AbortController();
    openController = controller;
    selected = object;
    focusEditorAfterOpen = focusEditor;
    detail = null;
    detailLoading = true;
    pdfMessage = null;
    showConnections = false;
    showColorPicker = false;
    splitEditorObject = null;
    splitEditorContent = '';
    splitEditorPrefix = '';
    splitEditorLastSaved = '';
    splitEditorSaveState = 'saved';
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
          error instanceof Error
            ? error.message
            : 'Unable to open this object.';
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

  function updateSplitContent(value: string): void {
    splitEditorContent = value;
    splitEditorSaveState = 'unsaved';
    if (splitSaveTimer) clearTimeout(splitSaveTimer);
    splitSaveTimer = setTimeout(() => void saveSplitNow(), 700);
  }

  async function selectSplitEditor(
    objectId: string,
    force = false
  ): Promise<void> {
    if (!selected || selected.type !== 'paper') return;
    const currentId = splitEditorObject?.id ?? selected.id;
    if (currentId === objectId && !force) return;

    if (splitEditorObject) {
      if (!(await flushSplitSave())) return;
    } else if (!(await flushSave())) {
      return;
    }

    if (objectId === selected.id) {
      splitEditorObject = null;
      splitEditorContent = '';
      splitEditorPrefix = '';
      splitEditorLastSaved = '';
      splitEditorSaveState = 'saved';
      showPreview = false;
      return;
    }

    const note = connectedNotes.find((item) => item.id === objectId);
    if (!note) return;
    splitEditorLoading = true;
    showPreview = false;
    try {
      const markdown = await getWorkspaceMarkdown(note.id);
      const editable = splitMarkdownDocument(markdown.content);
      splitEditorObject = note;
      splitEditorPrefix = editable.prefix;
      splitEditorContent = editable.body;
      splitEditorLastSaved = editable.body;
      splitEditorSaveState = 'saved';
    } catch (error) {
      listError =
        error instanceof Error ? error.message : 'Unable to open this note.';
    } finally {
      splitEditorLoading = false;
    }
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

  async function saveSplitNow(): Promise<void> {
    splitSaveRequested = true;
    if (splitSaveTask) return splitSaveTask;
    splitSaveTask = drainSplitSaves().finally(() => {
      splitSaveTask = null;
    });
    return splitSaveTask;
  }

  async function drainSplitSaves(): Promise<void> {
    while (splitSaveRequested) {
      splitSaveRequested = false;
      if (!splitEditorObject || splitEditorContent === splitEditorLastSaved) {
        continue;
      }
      const target = splitEditorObject.id;
      const snapshot = splitEditorContent;
      const prefix = splitEditorPrefix;
      splitEditorSaveState = 'saving';
      try {
        const saved = await saveWorkspaceMarkdown(
          target,
          `${prefix}${snapshot}`
        );
        if (splitEditorObject?.id !== target) continue;
        const editable = splitMarkdownDocument(saved.content);
        splitEditorPrefix = editable.prefix;
        splitEditorLastSaved = editable.body;
        splitEditorSaveState =
          splitEditorContent === editable.body ? 'saved' : 'unsaved';
      } catch {
        splitEditorSaveState = 'error';
        splitSaveRequested = false;
        break;
      }
    }
  }

  async function flushSplitSave(): Promise<boolean> {
    if (splitSaveTimer) clearTimeout(splitSaveTimer);
    if (!splitEditorObject) return true;
    await saveSplitNow();
    return splitEditorSaveState !== 'error';
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

  function createKindFromQuery(value: string | null): CreateKind | null {
    return value === 'note' ||
      value === 'brainstorm' ||
      value === 'concept' ||
      value === 'project'
      ? value
      : null;
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

  function updateSplitRatio(event: PointerEvent): void {
    if (!splitView) return;
    const bounds = splitView.getBoundingClientRect();
    const stacked = window.matchMedia('(max-width: 1100px)').matches;
    const position = stacked
      ? ((event.clientY - bounds.top) / bounds.height) * 100
      : ((event.clientX - bounds.left) / bounds.width) * 100;
    splitRatio = Math.min(75, Math.max(25, position));
  }

  function startSplitResize(event: PointerEvent): void {
    resizingSplit = true;
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
    updateSplitRatio(event);
  }

  function continueSplitResize(event: PointerEvent): void {
    if (resizingSplit) updateSplitRatio(event);
  }

  function stopSplitResize(event: PointerEvent): void {
    resizingSplit = false;
    const target = event.currentTarget as HTMLElement;
    if (target.hasPointerCapture(event.pointerId)) {
      target.releasePointerCapture(event.pointerId);
    }
  }

  function resizeSplitWithKeyboard(event: KeyboardEvent): void {
    const direction =
      event.key === 'ArrowLeft' || event.key === 'ArrowUp'
        ? -1
        : event.key === 'ArrowRight' || event.key === 'ArrowDown'
          ? 1
          : 0;
    if (!direction) return;
    event.preventDefault();
    splitRatio = Math.min(75, Math.max(25, splitRatio + direction * 5));
  }

  function clearSelection(): void {
    void flushSave();
    void flushSplitSave();
    openController?.abort();
    selected = null;
    detail = null;
    content = '';
    documentPrefix = '';
    lastSaved = '';
    splitEditorObject = null;
    splitEditorContent = '';
    splitEditorPrefix = '';
    splitEditorLastSaved = '';
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

  function wordCountFor(markdown: string): number {
    return markdown.trim() ? markdown.trim().split(/\s+/).length : 0;
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

  function openCreate(kind: CreateKind = 'note'): void {
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
    createKind = kind;
    createError = null;
    requestAnimationFrame(() => createInput?.focus());
  }

  async function createWriting(): Promise<void> {
    const title = createTitle.trim();
    if (!title || createBusy) return;
    createBusy = true;
    createError = null;

    try {
      let createdObject: LinkableObject;
      if (createKind === 'note') {
        createdObject = (await createStandaloneNote(title, createColor)).object;
        if (selected && coreTypes.has(selected.type)) {
          await createLinks(createdObject.id, [selected.id]);
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

  function objectColorHsl(object: LinkableObject): string {
    return object.type === 'note'
      ? noteColorHsl(object.color)
      : entityMeta[object.type].hslVar;
  }

  async function changeNoteColor(color: string): Promise<void> {
    if (!selected || selected.type !== 'note' || colorBusy) return;
    colorBusy = true;
    try {
      const response = await setObjectColor(selected.id, color);
      selected = response.object;
      showColorPicker = false;
      await loadList(query, activeFilter, true);
    } catch (error) {
      listError =
        error instanceof Error ? error.message : 'Unable to update note color.';
    } finally {
      colorBusy = false;
    }
  }

  async function handleLinked(): Promise<void> {
    if (!selected) return;
    await openObject(selected, false, true);
    await loadList(query, activeFilter, true);
    showConnections = false;
  }

  function connectionIdFor(item: LinkableObject): string {
    if (!selected || !detail) return '';
    const isOutgoing = Object.values(detail.related).some((group) =>
      group.some((candidate) => candidate.id === item.id)
    );
    return isOutgoing
      ? `${selected.id}=>${item.id}`
      : `${item.id}=>${selected.id}`;
  }

  async function removeConnection(item: LinkableObject): Promise<void> {
    if (!selected || connectionBusy) return;
    connectionBusy = item.id;
    try {
      await deleteConnection(connectionIdFor(item));
      await openObject(selected, false, true);
      await loadList(query, activeFilter, true);
    } catch (error) {
      listError =
        error instanceof Error ? error.message : 'Unable to remove connection.';
    } finally {
      connectionBusy = null;
    }
  }
</script>

{#snippet writingSurface(
  context: WorkspacePanelContext,
  title: string,
  objectId: string,
  compact = false
)}
  {@const editorWordCount = wordCountFor(context.content)}
  <div
    class="flex shrink-0 items-center justify-between border-b border-border/90 bg-surface/50 px-5 py-1.5"
  >
    <span
      class="inline-flex min-w-0 items-center gap-3 text-xs text-muted-foreground"
    >
      <span class="inline-flex items-center gap-2">
        <Cpu size={12} class="text-accent" />
        Writing surface
      </span>
      <span class="h-3 w-px bg-border"></span>
      <span>{editorWordCount} {editorWordCount === 1 ? 'word' : 'words'}</span>
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
        content={context.content}
        objectTitle={title}
        compact
        showMetadata={false}
      />
    </div>
  {:else}
    <div
      class={[
        'writing-stage min-h-0 flex-1 overflow-hidden',
        compact ? 'p-2' : 'p-3 sm:p-5'
      ]}
    >
      <div
        class={[
          'entity-writing-sheet h-full overflow-hidden border-x bg-surface/35 shadow-panel',
          compact ? 'max-w-none' : 'mx-auto max-w-5xl'
        ]}
      >
        {#key objectId}
          <MarkdownPanel
            {context}
            autofocus={focusEditorAfterOpen}
            placeholder={`Write in ${title}...`}
          />
        {/key}
      </div>
    </div>
  {/if}
{/snippet}

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
              <Plus size={13} /> New item
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
                    : 'border-border/80 bg-surface text-muted-foreground hover:text-foreground'
                ]}
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

          {#if createKind === 'note'}
            <div class="mt-3">
              <p class="text-[0.68rem] font-medium text-muted-foreground">
                Color
              </p>
              <div class="mt-1.5 flex items-center gap-2">
                {#each noteColors as color}
                  <button
                    type="button"
                    class="note-color-option"
                    class:note-color-option--active={createColor === color.id}
                    style={`--note-swatch: ${color.hsl}`}
                    aria-label={color.label}
                    aria-pressed={createColor === color.id}
                    title={color.label}
                    onclick={() => (createColor = color.id)}
                  ></button>
                {/each}
              </div>
            </div>
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
          <Plus size={16} /> New note or project
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

      <div class="mt-3 grid grid-cols-2 gap-1">
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
                style={`--thread-entity: ${objectColorHsl(item)}`}
                onclick={() => openObject(item)}
                ondragstart={(event) => startObjectDrag(event, item)}
              >
                <span
                  class="thread-icon"
                  style={`color: hsl(${objectColorHsl(item)})`}
                >
                  <Icon size={14} />
                </span>
                <span class="min-w-0 flex-1">
                  <span class="block truncate text-sm font-medium"
                    >{item.title}</span
                  >
                  <span
                    class="mt-0.5 block truncate text-[0.66rem] text-muted-foreground"
                  >
                    <span
                      style={item.type === 'note'
                        ? `color: hsl(${objectColorHsl(item)})`
                        : undefined}>{entityMeta[item.type].label}</span
                    >{item.subtitle ? ` · ${item.subtitle}` : ''}
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
  <main
    class={[
      'workspace-viewer flex min-w-0 flex-col overflow-hidden border border-transparent',
      selected ? 'ros-entity-context' : ''
    ]}
    style={selected
      ? `--entity-context: ${objectColorHsl(selected)}`
      : undefined}
  >
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
            onclick={() => openCreate('note')}
          >
            <Plus size={16} /> New note
          </button>
        </div>
      </div>
    {:else}
      {@const Icon = entityMeta[selected.type].icon}
      <header
        class="workspace-document-header ros-entity-panel flex items-center gap-3 border-b bg-surface/60 px-5 py-3 shadow-panel"
      >
        <span
          class="document-node"
          style={`color: hsl(${objectColorHsl(selected)})`}
        >
          <Icon size={17} />
        </span>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <span
              class={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium ${entityMeta[selected.type].badge}`}
              style={selected.type === 'note'
                ? `color: hsl(${objectColorHsl(selected)}); background: hsl(${objectColorHsl(selected)} / 0.1)`
                : undefined}
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
          {#if selected.type === 'note'}
            <div class="relative">
              <button
                type="button"
                class="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-muted/20 px-2.5 text-xs text-muted-foreground transition hover:text-foreground"
                aria-label="Change note color"
                aria-expanded={showColorPicker}
                onclick={() => (showColorPicker = !showColorPicker)}
              >
                <span
                  class="h-2.5 w-2.5 rounded-full"
                  style={`background: hsl(${noteColorHsl(selected.color)})`}
                ></span>
                <Palette size={13} />
              </button>
              {#if showColorPicker}
                <div
                  class="absolute right-0 top-10 z-30 flex gap-2 rounded-md border border-border bg-background p-2 shadow-lg"
                >
                  {#each noteColors as color}
                    <button
                      type="button"
                      class="note-color-option"
                      class:note-color-option--active={selected.color ===
                        color.id}
                      style={`--note-swatch: ${color.hsl}`}
                      aria-label={color.label}
                      title={color.label}
                      disabled={colorBusy}
                      onclick={() => changeNoteColor(color.id)}
                    ></button>
                  {/each}
                </div>
              {/if}
            </div>
          {/if}
          <button
            type="button"
            class="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-muted/20 px-2.5 text-xs text-muted-foreground transition hover:border-accent/40 hover:text-foreground"
            onclick={() => (showConnections = true)}
          >
            <Link2 size={13} />
            <span class="hidden sm:inline">Connect</span>
          </button>
          <button
            type="button"
            class="inline-flex h-8 items-center gap-1.5 rounded-md border border-entity-note/35 bg-entity-note/[0.08] px-2.5 text-xs text-entity-note transition hover:bg-entity-note/15"
            aria-label="Create a linked note"
            onclick={() => openCreate('note')}
          >
            <Plus size={13} /> <span class="hidden sm:inline">New note</span>
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
                ? 'entity-tab--active text-foreground'
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
                ? 'entity-tab--active text-foreground'
                : 'text-muted-foreground hover:text-foreground'
            ]}
            onclick={() => (viewerTab = 'notes')}
          >
            Reading note
          </button>
          <button
            type="button"
            class={[
              'rounded-md px-3 py-1 text-sm transition',
              viewerTab === 'split'
                ? 'entity-tab--active text-foreground'
                : 'text-muted-foreground hover:text-foreground'
            ]}
            onclick={() => (viewerTab = 'split')}
          >
            PDF + note
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
            <PdfReader objectId={selected.id} title={selected.title} url={selectedPdfUrl} />
          {/key}
        {:else if isPaper && viewerTab === 'split' && editorContext}
          <div
            bind:this={splitView}
            class="workspace-split min-h-0 flex-1 overflow-hidden"
            class:is-resizing={resizingSplit}
            style={`--split-position: ${splitRatio}%`}
          >
            <section
              class="split-pane min-h-0 overflow-hidden"
              aria-label="PDF"
            >
              {#key selectedPdfUrl}
                <PdfReader objectId={selected.id} title={selected.title} url={selectedPdfUrl} />
              {/key}
            </section>
            <button
              type="button"
              class="split-divider"
              aria-label={`Resize PDF and notes panels, PDF ${Math.round(splitRatio)} percent`}
              onpointerdown={startSplitResize}
              onpointermove={continueSplitResize}
              onpointerup={stopSplitResize}
              onpointercancel={stopSplitResize}
              onkeydown={resizeSplitWithKeyboard}
            >
              <span aria-hidden="true"></span>
            </button>
            <section
              class="split-pane flex min-h-0 min-w-0 flex-col overflow-hidden"
              aria-label="Notes"
            >
              <div
                class="flex shrink-0 items-center justify-between gap-3 border-b border-border/90 bg-surface/70 px-4 py-2"
              >
                <label
                  class="flex min-w-0 flex-1 items-center gap-2 text-xs text-muted-foreground"
                >
                  <span class="shrink-0">Write in</span>
                  <select
                    class="h-8 min-w-0 max-w-72 flex-1 rounded-md border border-border bg-background px-2 text-xs text-foreground outline-none focus:border-accent/55"
                    value={splitEditorObject?.id ?? selected.id}
                    disabled={splitEditorLoading}
                    onchange={(event) =>
                      selectSplitEditor(event.currentTarget.value)}
                  >
                    <option value={selected.id}>Reading note (PDF)</option>
                    {#each connectedNotes as note (note.id)}
                      <option value={note.id}>{note.title}</option>
                    {/each}
                  </select>
                </label>
                <span class="shrink-0 text-[0.68rem] text-muted-foreground">
                  {splitEditorObject
                    ? splitEditorSaveState === 'saving'
                      ? 'Saving...'
                      : splitEditorSaveState === 'error'
                        ? 'Save failed'
                        : 'Saved'
                    : saveState === 'saving'
                      ? 'Saving...'
                      : saveState === 'error'
                        ? 'Save failed'
                        : 'Saved'}
                </span>
              </div>
              {#if splitEditorLoading}
                <p class="p-5 text-sm text-muted-foreground">Opening note...</p>
              {:else if activeSplitContext}
                {@render writingSurface(
                  activeSplitContext,
                  splitEditorObject?.title ?? selected.title,
                  splitEditorObject?.id ?? selected.id,
                  true
                )}
              {/if}
            </section>
          </div>
        {:else if projectContext}
          <ProjectDashboard context={projectContext} />
        {:else if editorContext}
          <!-- Markdown editor / preview (notes, ideas, projects, concepts) -->
          {@render writingSurface(editorContext, selected.title, selected.id)}
        {/if}

        {#if detail && (relatedItems.length || (detail.tags?.length ?? 0))}
          <footer class="entity-footer border-t px-5 py-3">
            <TagBadges tags={detail.tags} />
            {#if relatedItems.length}
              <div class="mt-2 flex flex-wrap items-center gap-1.5">
                <span class="text-xs text-muted-foreground">Connections:</span>
                {#each relatedItems.slice(0, 8) as related (related.id)}
                  {@const RelIcon = entityMeta[related.type].icon}
                  <span
                    class={`inline-flex items-center rounded-md border text-xs text-muted-foreground ${entityMeta[related.type].border} ${entityMeta[related.type].tint}`}
                  >
                    <button
                      type="button"
                      class="inline-flex min-w-0 items-center gap-1 px-2 py-0.5 transition hover:text-foreground"
                      onclick={() => openObject(related)}
                    >
                      <RelIcon
                        size={11}
                        class={entityMeta[related.type].text}
                      />
                      <span class="max-w-40 truncate">{related.title}</span>
                    </button>
                    <button
                      type="button"
                      class="border-l border-border/60 px-1.5 py-0.5 transition hover:text-entity-review disabled:opacity-40"
                      aria-label={`Remove connection to ${related.title}`}
                      disabled={connectionBusy === related.id}
                      onclick={() => removeConnection(related)}
                    >
                      <X size={10} />
                    </button>
                  </span>
                {/each}
              </div>
            {/if}
          </footer>
        {/if}
      </div>
    {/if}
  </main>

  {#if showConnections && selected}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        class="absolute inset-0 bg-black/60"
        aria-label="Close connections"
        onclick={() => (showConnections = false)}
      ></button>
      <div
        class="relative z-10 max-h-[85vh] w-full max-w-xl overflow-auto rounded-lg border border-border bg-background p-5 shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="connect-title"
      >
        <div class="mb-4 flex items-start justify-between gap-4">
          <div>
            <p class="text-xs font-medium uppercase text-accent">Connect</p>
            <h2 id="connect-title" class="mt-1 text-lg font-semibold">
              {selected.title}
            </h2>
            <p class="mt-1 text-sm text-muted-foreground">
              Link this item to a note, paper or project.
            </p>
          </div>
          <button
            type="button"
            class="ros-btn-icon"
            aria-label="Close connections"
            onclick={() => (showConnections = false)}
          >
            <X size={15} />
          </button>
        </div>
        <LinkPicker
          sourceId={selected.id}
          allowedTypes={connectionTypes}
          excludeIds={connectedIds}
          on:linked={handleLinked}
        />
      </div>
    </div>
  {/if}
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
    border-color: hsl(var(--thread-entity) / 0.42);
    background: hsl(var(--thread-entity) / 0.1);
    box-shadow: inset 2px 0 0 hsl(var(--thread-entity) / 0.72);
  }

  .thread-icon {
    position: relative;
    z-index: 1;
    width: 28px;
    height: 28px;
    background: hsl(var(--surface));
    border-color: hsl(var(--thread-entity) / 0.28);
  }

  .thread-port {
    width: 6px;
    height: 6px;
    margin-top: 11px;
    border: 1px solid hsl(var(--thread-entity) / 0.5);
    background: hsl(var(--background));
  }

  .workspace-thread--active .thread-port {
    background: hsl(var(--thread-entity));
    box-shadow: 0 0 8px hsl(var(--thread-entity) / 0.55);
  }

  .workspace-viewer {
    background: hsl(var(--background) / 0.93);
  }

  .workspace-viewer.ros-entity-context {
    background:
      linear-gradient(
        135deg,
        hsl(var(--entity-context) / 0.045),
        transparent 25%
      ),
      hsl(var(--background) / 0.96);
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
    background: linear-gradient(
      90deg,
      hsl(var(--entity-context) / 0.85),
      hsl(var(--entity-context) / 0.16),
      transparent
    );
  }

  .document-node {
    width: 36px;
    height: 36px;
    border-color: hsl(var(--entity-context) / 0.45);
    background: hsl(var(--entity-context) / 0.08);
    box-shadow: inset 0 0 12px hsl(var(--entity-context) / 0.06);
  }

  .entity-tab--active {
    border: 1px solid hsl(var(--entity-context) / 0.32);
    background: hsl(var(--entity-context) / 0.11);
  }

  .workspace-split {
    display: grid;
    grid-template-columns:
      minmax(0, var(--split-position)) 8px
      minmax(0, 1fr);
  }

  .split-pane {
    background: hsl(var(--background) / 0.94);
  }

  .split-divider {
    position: relative;
    z-index: 2;
    cursor: col-resize;
    touch-action: none;
    border: 0;
    padding: 0;
    background: hsl(var(--border) / 0.75);
    outline: none;
    transition: background-color 120ms ease;
  }

  .split-divider::before {
    content: '';
    position: absolute;
    inset: 0 -3px;
  }

  .split-divider span {
    position: absolute;
    left: 50%;
    top: 50%;
    width: 2px;
    height: 42px;
    border-radius: 999px;
    background: hsl(var(--muted-foreground) / 0.55);
    transform: translate(-50%, -50%);
  }

  .split-divider:hover,
  .split-divider:focus-visible,
  .is-resizing .split-divider {
    background: hsl(var(--accent) / 0.5);
  }

  .is-resizing {
    user-select: none;
  }

  .entity-writing-sheet {
    border-color: hsl(var(--entity-context) / 0.3);
    box-shadow:
      inset 0 1px 0 hsl(var(--entity-context) / 0.08),
      0 12px 36px hsl(210 20% 2% / 0.18);
  }

  .entity-footer {
    border-color: hsl(var(--entity-context) / 0.28);
    background: hsl(var(--entity-context) / 0.025);
  }

  .note-color-option {
    width: 22px;
    height: 22px;
    flex: 0 0 auto;
    border: 2px solid hsl(var(--background));
    border-radius: 999px;
    background: hsl(var(--note-swatch));
    box-shadow: 0 0 0 1px hsl(var(--border));
    transition:
      transform 120ms ease,
      box-shadow 120ms ease;
  }

  .note-color-option:hover,
  .note-color-option:focus-visible {
    transform: scale(1.12);
    outline: none;
  }

  .note-color-option--active {
    box-shadow:
      0 0 0 2px hsl(var(--background)),
      0 0 0 4px hsl(var(--note-swatch));
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

  @media (max-width: 1100px) {
    .workspace-split {
      grid-template-columns: minmax(0, 1fr);
      grid-template-rows:
        minmax(220px, var(--split-position)) 8px
        minmax(280px, 1fr);
    }

    .split-divider {
      cursor: row-resize;
    }

    .split-divider span {
      width: 42px;
      height: 2px;
    }
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
