<script lang="ts">
  import {
    BookOpen,
    Boxes,
    Brain,
    Check,
    FileText,
    FolderInput,
    GitBranch,
    Lightbulb,
    LoaderCircle,
    Network,
    PenLine,
    Plus,
    Search,
    Sparkles,
    X
  } from '@lucide/svelte';

  import { entityMeta } from '$lib/design/entities';
  import ProjectAssistantPanel from '$lib/features/assistant/components/ProjectAssistantPanel.svelte';
  import { createConcept } from '$lib/features/concepts/services/conceptsApi';
  import { createLinks } from '$lib/features/linking/services/linkingApi';
  import type {
    LinkableObject,
    LinkableType
  } from '$lib/features/linking/types/linking';
  import MarkdownPreview from '$lib/features/research-workspace/MarkdownPreview.svelte';
  import type { CorpusEntry } from '$lib/features/research-explorer/types/researchExplorer';
  import ProjectBrainHub, {
    type ProjectBrainHubTarget
  } from '$lib/features/workspace/components/ProjectBrainHub.svelte';
  import MarkdownPanel from '$lib/features/workspace/panels/MarkdownPanel.svelte';
  import {
    createBrainstorm,
    createWorkspaceNote,
    listWorkspaceNotes,
    setWorkspaceProject,
    type WorkspaceNote
  } from '$lib/features/workspace/services/workspaceApi';
  import type { WorkspacePanelContext } from '$lib/features/workspace/types/panels';

  type Props = {
    context: WorkspacePanelContext;
  };

  type ProjectNotePreview = {
    paper: LinkableObject;
    note: WorkspaceNote;
  };

  type IntakeMode = 'existing' | 'create';
  type IntakeFilter = 'all' | Exclude<LinkableType, 'project'>;
  type ProjectCreateKind = 'note' | 'brainstorm' | 'concept';

  const metadataKeys = ['status', 'priority', 'domain', 'method', 'tags'];
  const intakeFilters: IntakeFilter[] = [
    'all',
    'paper',
    'note',
    'concept',
    'brainstorm',
    'review'
  ];
  const projectCreateKinds: ProjectCreateKind[] = [
    'note',
    'brainstorm',
    'concept'
  ];

  let { context }: Props = $props();
  let noteMode = $state<'reading' | 'editing'>('reading');
  let assistantOpen = $state(false);
  let projectNotes = $state<ProjectNotePreview[]>([]);
  let intakeOpen = $state(false);
  let intakeMode = $state<IntakeMode>('existing');
  let intakeFilter = $state<IntakeFilter>('all');
  let intakeQuery = $state('');
  let intakeResults = $state<LinkableObject[]>([]);
  let intakeSearching = $state(false);
  let intakeBusy = $state('');
  let intakeMessage = $state<string | null>(null);
  let intakeError = $state<string | null>(null);
  let createKind = $state<ProjectCreateKind>('note');
  let createTitle = $state('');
  let dropActive = $state(false);
  let intakeSearchTimer: ReturnType<typeof setTimeout> | null = null;
  let papersSection = $state<HTMLElement | null>(null);
  let notesSection = $state<HTMLElement | null>(null);
  let graphSection = $state<HTMLElement | null>(null);
  let ideasSection = $state<HTMLElement | null>(null);
  let briefSection = $state<HTMLElement | null>(null);

  function unique(items: LinkableObject[]): LinkableObject[] {
    const seen = new Set<string>();
    return items.filter((item) => {
      if (item.id === context.object.id || seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });
  }

  function fallbackEntries(type: LinkableType): CorpusEntry[] {
    return unique([
      ...(context.detail?.related[type] ?? []),
      ...(context.detail?.backlinks[type] ?? [])
    ])
      .sort((a, b) => a.title.localeCompare(b.title))
      .map((object) => ({ object, roles: [] }));
  }

  function entries(type: LinkableType): CorpusEntry[] {
    const corpus = context.detail?.corpus?.[type];
    if (corpus?.length) {
      return [...corpus].sort((a, b) =>
        a.object.title.localeCompare(b.object.title)
      );
    }
    return fallbackEntries(type);
  }

  function metadataValue(key: string): string {
    const value = context.detail?.metadata?.[key]?.trim();
    return value ? value.replace(/^\[(.*)\]$/, '$1') : 'Not set';
  }

  function hasRole(entry: CorpusEntry, roles: string[]): boolean {
    return roles.some((role) => entry.roles.includes(role));
  }

  function relationCount(): number {
    return (
      papers.length +
      concepts.length +
      researchIdeas.length +
      reviews.length +
      linkedNotes.length +
      projectNotes.length
    );
  }

  function markdownStem(path: string): string {
    return (path.split(/[\\/]/).pop() ?? path).replace(/\.md$/i, '');
  }

  function intakeLabel(filter: IntakeFilter): string {
    return filter === 'all' ? 'All' : entityMeta[filter].plural;
  }

  function scheduleIntakeSearch(): void {
    if (intakeSearchTimer) clearTimeout(intakeSearchTimer);
    intakeSearchTimer = setTimeout(() => void loadIntakeResults(), 140);
  }

  async function loadIntakeResults(): Promise<void> {
    intakeSearching = true;
    intakeError = null;
    try {
      const results = await context.searchObjects(intakeQuery);
      const attached = new Set(
        (context.detail?.all_related ?? []).map((item) => item.id)
      );
      intakeResults = results.filter(
        (item) =>
          item.id !== context.object.id &&
          item.type !== 'project' &&
          !attached.has(item.id) &&
          (intakeFilter === 'all' || item.type === intakeFilter)
      );
    } catch (error) {
      intakeResults = [];
      intakeError =
        error instanceof Error
          ? error.message
          : 'Unable to load project material.';
    } finally {
      intakeSearching = false;
    }
  }

  async function attachObject(item: LinkableObject): Promise<void> {
    if (intakeBusy) return;
    intakeBusy = item.id;
    intakeMessage = null;
    intakeError = null;
    try {
      if (item.type === 'paper') {
        await setWorkspaceProject(item.id, context.object.id);
      } else {
        await createLinks(context.object.id, [item.id]);
      }
      intakeResults = intakeResults.filter((result) => result.id !== item.id);
      intakeMessage = `${item.title} added to the project.`;
      await context.refreshObject();
    } catch (error) {
      intakeError =
        error instanceof Error ? error.message : 'Unable to add this material.';
    } finally {
      intakeBusy = '';
      dropActive = false;
    }
  }

  async function createInProject(): Promise<void> {
    const title = createTitle.trim();
    if (!title || intakeBusy) return;
    intakeBusy = `create-${createKind}`;
    intakeMessage = null;
    intakeError = null;
    try {
      let createdObject: LinkableObject;
      if (createKind === 'note') {
        const created = await createWorkspaceNote(context.object.id, title);
        createdObject = {
          id: `note:${markdownStem(created.object.markdown_path)}::${created.note.id}`,
          type: 'note',
          title: created.note.title,
          subtitle: created.object.title,
          markdown_path: created.note.path
        };
      } else if (createKind === 'brainstorm') {
        createdObject = (await createBrainstorm(title)).object;
      } else {
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
      }

      await createLinks(context.object.id, [createdObject.id]);
      createTitle = '';
      await context.refreshObject();
      await context.openObject(createdObject);
    } catch (error) {
      intakeError =
        error instanceof Error
          ? error.message
          : 'Unable to create this object.';
    } finally {
      intakeBusy = '';
    }
  }

  function handleDragOver(event: DragEvent): void {
    if (!event.dataTransfer?.types.includes('application/x-research-object'))
      return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
    dropActive = true;
  }

  function handleDragLeave(event: DragEvent): void {
    const nextTarget = event.relatedTarget;
    if (nextTarget instanceof Node && event.currentTarget instanceof Node) {
      if (event.currentTarget.contains(nextTarget)) return;
    }
    dropActive = false;
  }

  function handleDrop(event: DragEvent): void {
    event.preventDefault();
    dropActive = false;
    const raw = event.dataTransfer?.getData('application/x-research-object');
    if (!raw) return;
    try {
      const item = JSON.parse(raw) as LinkableObject;
      if (item.id && item.type !== 'project') void attachObject(item);
    } catch {
      intakeError = 'This item could not be added to the project.';
    }
  }

  async function loadProjectNotes(): Promise<void> {
    const previews: ProjectNotePreview[] = [];
    const directlyLinkedPaths = new Set(
      linkedNotes.map((entry) => entry.object.markdown_path)
    );
    for (const entry of papers.slice(0, 8)) {
      const response = await listWorkspaceNotes(entry.object.id).catch(
        () => null
      );
      if (!response) continue;
      for (const note of response.notes.slice(0, 3)) {
        if (directlyLinkedPaths.has(note.path)) continue;
        previews.push({ paper: entry.object, note });
      }
    }
    projectNotes = previews.slice(0, 8);
  }

  function focusSection(target: ProjectBrainHubTarget): void {
    const sectionByTarget: Record<ProjectBrainHubTarget, HTMLElement | null> = {
      papers: papersSection,
      notes: notesSection,
      graph: graphSection,
      ideas: ideasSection,
      brief: briefSection
    };
    sectionByTarget[target]?.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  }

  let papers = $derived(entries('paper'));
  let continueReading = $derived(
    papers.filter((entry) => hasRole(entry, ['Reading'])).slice(0, 4)
  );
  let unreadPapers = $derived(
    papers.filter((entry) => hasRole(entry, ['To Read'])).slice(0, 4)
  );
  let reviewedPapers = $derived(
    papers.filter((entry) => hasRole(entry, ['Reviewed', 'Cited']))
  );
  let concepts = $derived(entries('concept'));
  let researchIdeas = $derived(entries('brainstorm'));
  let reviews = $derived(entries('review'));
  let linkedNotes = $derived(entries('note'));
  let visibleReading = $derived(
    continueReading.length ? continueReading : papers.slice(0, 4)
  );
  let isolatedPapers = $derived(
    papers.filter((entry) => !entry.roles.length).length
  );

  $effect(() => {
    if (!intakeOpen || intakeMode !== 'existing') return;
    void intakeQuery;
    void intakeFilter;
    scheduleIntakeSearch();
    return () => {
      if (intakeSearchTimer) clearTimeout(intakeSearchTimer);
    };
  });

  $effect(() => {
    void context.object.id;
    void papers.map((entry) => entry.object.id).join('|');
    void loadProjectNotes();
  });
</script>

<section class="flex min-h-0 flex-1 flex-col overflow-auto bg-background/95">
  <div class="border-b border-border px-6 py-5">
    <div class="flex min-w-0 flex-wrap items-start justify-between gap-4">
      <div class="min-w-0">
        <div class="flex items-center gap-2">
          <Boxes size={17} class={entityMeta.project.text} />
          <p class="text-xs font-medium uppercase text-accent">
            Research Workspace
          </p>
        </div>
        <h3 class="mt-1 text-xl font-semibold text-foreground">
          {context.object.title}
        </h3>
        {#if context.detail?.description}
          <p class="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            {context.detail.description}
          </p>
        {/if}
      </div>
      <div class="flex items-center gap-2">
        <span
          class="rounded-md border border-border bg-muted/20 px-2 py-1 text-xs text-muted-foreground"
        >
          {relationCount()} items
        </span>
        <button
          type="button"
          class={assistantOpen
            ? 'inline-flex h-8 items-center gap-1.5 rounded-md border border-accent/45 bg-accent/15 px-2.5 text-xs font-semibold text-accent'
            : 'inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-muted/20 px-2.5 text-xs text-muted-foreground transition hover:border-accent/40 hover:text-foreground'}
          aria-expanded={assistantOpen}
          onclick={() => (assistantOpen = !assistantOpen)}
        >
          <Sparkles size={13} /> Assistant
        </button>
        <button
          type="button"
          class="inline-flex h-8 items-center gap-1.5 rounded-md border border-accent/40 bg-accent/10 px-2.5 text-xs font-semibold text-accent transition hover:bg-accent/15"
          aria-expanded={intakeOpen}
          onclick={() => (intakeOpen = !intakeOpen)}
        >
          {#if intakeOpen}<X size={13} /> Close{:else}<Plus size={13} /> Add material{/if}
        </button>
      </div>
    </div>

    <dl class="mt-5 grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
      {#each metadataKeys as key}
        {@const value = metadataValue(key)}
        <div class="rounded-md border border-border bg-muted/[0.08] px-3 py-2">
          <dt class="text-[0.68rem] uppercase text-muted-foreground">
            {key}
          </dt>
          <dd
            class={value === 'Not set'
              ? 'mt-1 truncate text-sm text-muted-foreground/60'
              : 'mt-1 truncate text-sm text-foreground'}
          >
            {value}
          </dd>
        </div>
      {/each}
    </dl>
  </div>

  {#if assistantOpen}
    <ProjectAssistantPanel
      project={context.object}
      openObject={context.openObject}
      refreshProject={context.refreshObject}
    />
  {/if}

  <section class="border-b border-border bg-surface/35 px-6 py-4">
    <div
      role="region"
      aria-label="Drop material into project"
      class={[
        'flex min-h-16 flex-wrap items-center justify-between gap-3 border border-dashed px-4 py-3 transition',
        dropActive
          ? 'border-accent bg-accent/12 shadow-[inset_0_0_24px_hsl(var(--accent)/0.08)]'
          : 'border-border bg-muted/[0.05]'
      ]}
      ondragover={handleDragOver}
      ondragleave={handleDragLeave}
      ondrop={handleDrop}
    >
      <div class="flex min-w-0 items-center gap-3">
        <span
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-accent/30 bg-accent/10 text-accent"
        >
          {#if intakeBusy}
            <LoaderCircle size={16} class="animate-spin" />
          {:else}
            <FolderInput size={16} />
          {/if}
        </span>
        <div class="min-w-0">
          <p class="text-sm font-semibold text-foreground">Project intake</p>
          <p class="mt-0.5 text-xs text-muted-foreground">
            Drag notes, concepts, brainstorms or PDFs from the Active desk.
          </p>
        </div>
      </div>
      <button
        type="button"
        class="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-background px-2.5 text-xs text-muted-foreground transition hover:border-accent/45 hover:text-foreground"
        onclick={() => (intakeOpen = true)}
      >
        <Search size={13} /> Browse all material
      </button>
    </div>

    {#if intakeMessage}
      <p class="mt-2 inline-flex items-center gap-1.5 text-xs text-accent">
        <Check size={13} />
        {intakeMessage}
      </p>
    {/if}
    {#if intakeError}
      <p class="mt-2 text-xs text-entity-review">{intakeError}</p>
    {/if}

    {#if intakeOpen}
      <div class="mt-4 border-t border-border/80 pt-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div
            class="flex items-center gap-1 rounded-md border border-border bg-muted/15 p-1"
            aria-label="Project intake mode"
          >
            <button
              type="button"
              class={intakeMode === 'existing'
                ? 'h-7 rounded bg-background px-3 text-xs font-medium text-foreground shadow-sm'
                : 'h-7 rounded px-3 text-xs text-muted-foreground hover:text-foreground'}
              onclick={() => (intakeMode = 'existing')}
            >
              Existing material
            </button>
            <button
              type="button"
              class={intakeMode === 'create'
                ? 'h-7 rounded bg-background px-3 text-xs font-medium text-foreground shadow-sm'
                : 'h-7 rounded px-3 text-xs text-muted-foreground hover:text-foreground'}
              onclick={() => (intakeMode = 'create')}
            >
              Create here
            </button>
          </div>
          <span class="text-xs text-muted-foreground">
            Everything added here stays linked to {context.object.title}.
          </span>
        </div>

        {#if intakeMode === 'existing'}
          <div
            class="mt-3 grid gap-3 lg:grid-cols-[minmax(220px,0.7fr)_minmax(0,1.3fr)]"
          >
            <div>
              <label
                class="flex h-10 items-center gap-2 rounded-md border border-border bg-background px-3 text-sm text-muted-foreground focus-within:border-accent/50"
              >
                <Search size={15} />
                <input
                  bind:value={intakeQuery}
                  class="min-w-0 flex-1 bg-transparent text-foreground outline-none"
                  placeholder="Search the complete Library..."
                />
                {#if intakeQuery}
                  <button
                    type="button"
                    class="rounded p-0.5 hover:bg-muted"
                    aria-label="Clear material search"
                    onclick={() => (intakeQuery = '')}
                  >
                    <X size={13} />
                  </button>
                {/if}
              </label>
              <div class="mt-2 grid grid-cols-3 gap-1">
                {#each intakeFilters as filter}
                  <button
                    type="button"
                    class={[
                      'h-7 min-w-0 truncate rounded-md border px-1.5 text-[0.65rem] transition',
                      intakeFilter === filter
                        ? 'border-accent/45 bg-accent/10 text-foreground'
                        : 'border-border bg-muted/[0.08] text-muted-foreground hover:text-foreground'
                    ]}
                    onclick={() => (intakeFilter = filter)}
                  >
                    {intakeLabel(filter)}
                  </button>
                {/each}
              </div>
            </div>

            <div
              class="max-h-56 overflow-y-auto border-l border-border/80 pl-3 lg:min-h-32"
            >
              {#if intakeSearching}
                <p
                  class="flex items-center gap-2 px-2 py-3 text-sm text-muted-foreground"
                >
                  <LoaderCircle size={14} class="animate-spin" /> Searching...
                </p>
              {:else if intakeResults.length === 0}
                <p class="px-2 py-3 text-sm text-muted-foreground">
                  No unlinked material matches this search.
                </p>
              {:else}
                <div class="grid gap-1.5 sm:grid-cols-2">
                  {#each intakeResults as item (item.id)}
                    {@const ItemIcon = entityMeta[item.type].icon}
                    <div
                      class="flex min-w-0 items-center gap-2 border border-border bg-background/70 px-2.5 py-2"
                    >
                      <ItemIcon size={14} class={entityMeta[item.type].text} />
                      <span class="min-w-0 flex-1">
                        <span
                          class="block truncate text-xs font-medium text-foreground"
                        >
                          {item.title}
                        </span>
                        <span
                          class="block text-[0.62rem] text-muted-foreground"
                        >
                          {entityMeta[item.type].label}
                        </span>
                      </span>
                      <button
                        type="button"
                        class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-border text-muted-foreground transition hover:border-accent/45 hover:text-accent"
                        aria-label={`Add ${item.title} to project`}
                        disabled={Boolean(intakeBusy)}
                        onclick={() => attachObject(item)}
                      >
                        {#if intakeBusy === item.id}
                          <LoaderCircle size={13} class="animate-spin" />
                        {:else}
                          <Plus size={13} />
                        {/if}
                      </button>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          </div>
        {:else}
          <div
            class="mt-3 grid gap-3 sm:grid-cols-[minmax(180px,0.45fr)_minmax(0,1fr)]"
          >
            <div class="grid grid-cols-3 gap-1 sm:grid-cols-1">
              {#each projectCreateKinds as kind}
                {@const CreateIcon = entityMeta[kind].icon}
                <button
                  type="button"
                  class={[
                    'flex h-9 min-w-0 items-center justify-center gap-1.5 rounded-md border px-2 text-xs transition sm:justify-start',
                    createKind === kind
                      ? `${entityMeta[kind].border} ${entityMeta[kind].tint} text-foreground`
                      : 'border-border bg-muted/[0.08] text-muted-foreground hover:text-foreground'
                  ]}
                  onclick={() => (createKind = kind)}
                >
                  <CreateIcon size={13} class={entityMeta[kind].text} />
                  <span class="truncate">{entityMeta[kind].label}</span>
                </button>
              {/each}
            </div>
            <div class="flex min-w-0 flex-col justify-center">
              <label
                class="text-xs font-medium text-foreground"
                for="project-create-title"
              >
                New {entityMeta[createKind].label} in {context.object.title}
              </label>
              <div class="mt-2 flex min-w-0 gap-2">
                <input
                  id="project-create-title"
                  bind:value={createTitle}
                  class="h-10 min-w-0 flex-1 rounded-md border border-border bg-background px-3 text-sm text-foreground outline-none focus:border-accent/55"
                  placeholder={`${entityMeta[createKind].label} title...`}
                  onkeydown={(event) =>
                    event.key === 'Enter' && createInProject()}
                />
                <button
                  type="button"
                  class="inline-flex h-10 shrink-0 items-center gap-1.5 rounded-md bg-accent px-3 text-xs font-semibold text-accent-foreground disabled:opacity-50"
                  disabled={!createTitle.trim() || Boolean(intakeBusy)}
                  onclick={createInProject}
                >
                  {#if intakeBusy.startsWith('create-')}
                    <LoaderCircle size={13} class="animate-spin" />
                  {:else}
                    <Plus size={13} />
                  {/if}
                  Create & open
                </button>
              </div>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </section>

  <ProjectBrainHub
    paperCount={papers.length}
    noteCount={linkedNotes.length + projectNotes.length}
    conceptCount={concepts.length}
    ideaCount={researchIdeas.length}
    reviewCount={reviews.length}
    relationCount={relationCount()}
    onSelect={focusSection}
  />

  <div
    class="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-5 px-6 py-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.9fr)]"
  >
    <div class="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-5">
      <section bind:this={papersSection} class="scroll-mt-5">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <BookOpen size={16} class={entityMeta.paper.text} />
            <h4 class="text-sm font-semibold text-foreground">
              Continue Reading
            </h4>
          </div>
          <span class="text-xs text-muted-foreground">
            {continueReading.length || papers.length}
          </span>
        </div>

        <div class="mt-3 grid grid-cols-[minmax(0,1fr)] gap-3 md:grid-cols-2">
          {#each visibleReading as entry}
            <button
              class="min-h-24 min-w-0 w-full rounded-lg border border-border bg-muted/[0.06] px-3 py-3 text-left transition hover:bg-muted/35"
              type="button"
              onclick={() => context.openObject(entry.object)}
            >
              <span class="line-clamp-2 text-sm font-medium text-foreground">
                {entry.object.title}
              </span>
              <span class="mt-2 flex flex-wrap gap-1">
                {#each entry.roles.slice(0, 3) as role}
                  <span
                    class="rounded border border-border bg-background px-1.5 py-0.5 text-[10px] uppercase text-muted-foreground"
                  >
                    {role}
                  </span>
                {/each}
              </span>
              {#if entry.object.subtitle}
                <span class="mt-2 block truncate text-xs text-muted-foreground">
                  {entry.object.subtitle}
                </span>
              {/if}
            </button>
          {:else}
            <p
              class="rounded-lg border border-dashed border-border px-3 py-5 text-sm text-muted-foreground"
            >
              Add papers to this project to create a reading desk.
            </p>
          {/each}
        </div>
      </section>

      <section bind:this={notesSection} class="scroll-mt-5">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <FileText size={16} class="text-entity-note" />
            <h4 class="text-sm font-semibold text-foreground">Recent Notes</h4>
          </div>
          <span class="text-xs text-muted-foreground">
            {linkedNotes.length + projectNotes.length}
          </span>
        </div>

        <div class="mt-3 grid grid-cols-[minmax(0,1fr)] gap-2 md:grid-cols-2">
          {#each linkedNotes as entry}
            <button
              class="min-w-0 w-full rounded-lg border border-entity-note/25 bg-entity-note/[0.07] px-3 py-2 text-left hover:bg-entity-note/12"
              type="button"
              onclick={() => context.openObject(entry.object)}
            >
              <span class="block truncate text-sm font-medium text-foreground">
                {entry.object.title}
              </span>
              <span class="mt-1 block truncate text-xs text-entity-note">
                Project note
              </span>
            </button>
          {/each}
          {#each projectNotes as preview}
            <button
              class="min-w-0 w-full rounded-lg border border-entity-note/20 bg-entity-note/[0.05] px-3 py-2 text-left hover:bg-entity-note/10"
              type="button"
              onclick={() => context.openObject(preview.paper)}
            >
              <span class="block truncate text-sm font-medium text-foreground">
                {preview.note.title}
              </span>
              <span class="mt-1 block truncate text-xs text-muted-foreground">
                {preview.paper.title}
              </span>
            </button>
          {/each}
          {#if linkedNotes.length === 0 && projectNotes.length === 0}
            <p
              class="rounded-lg border border-dashed border-border px-3 py-5 text-sm text-muted-foreground"
            >
              Create a project note here or attach an existing research note.
            </p>
          {/if}
        </div>
      </section>

      <section bind:this={graphSection} class="scroll-mt-5">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <Network size={16} class="text-accent" />
            <h4 class="text-sm font-semibold text-foreground">
              Knowledge Graph
            </h4>
          </div>
          <span class="text-xs text-muted-foreground">
            {relationCount()} signals
          </span>
        </div>

        <div
          class="mt-3 grid gap-3 rounded-lg border border-border bg-muted/[0.06] p-3 md:grid-cols-4"
        >
          <div>
            <p class="text-2xl font-semibold text-foreground">
              {papers.length}
            </p>
            <p class="mt-1 text-xs text-muted-foreground">Papers</p>
          </div>
          <div>
            <p class="text-2xl font-semibold text-foreground">
              {linkedNotes.length + projectNotes.length}
            </p>
            <p class="mt-1 text-xs text-entity-note">Notes</p>
          </div>
          <div>
            <p class="text-2xl font-semibold text-foreground">
              {researchIdeas.length}
            </p>
            <p class="mt-1 text-xs text-entity-brainstorm">Ideas</p>
          </div>
          <div>
            <p class="text-2xl font-semibold text-foreground">
              {isolatedPapers}
            </p>
            <p class="mt-1 text-xs text-muted-foreground">Unclassified</p>
          </div>
        </div>

        <div class="mt-3 flex flex-wrap gap-2">
          <span
            class="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2 py-1 text-xs text-muted-foreground"
          >
            <GitBranch size={12} />
            {reviewedPapers.length} reviewed papers
          </span>
          <span
            class="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2 py-1 text-xs text-muted-foreground"
          >
            <Brain size={12} />
            {concepts.length} extracted concepts
          </span>
          <span
            class="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2 py-1 text-xs text-muted-foreground"
          >
            <BookOpen size={12} />
            {unreadPapers.length} unread papers
          </span>
        </div>
      </section>
    </div>

    <aside class="grid min-w-0 grid-cols-[minmax(0,1fr)] content-start gap-5">
      <section bind:this={ideasSection} class="scroll-mt-5">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <Lightbulb size={16} class={entityMeta.brainstorm.text} />
            <h4 class="text-sm font-semibold text-foreground">
              Research Ideas
            </h4>
          </div>
          <span class="text-xs text-muted-foreground">
            {researchIdeas.length}
          </span>
        </div>
        <div class="mt-3 grid gap-2">
          {#each researchIdeas.slice(0, 6) as entry}
            <button
              class="rounded-md border border-border bg-muted/[0.06] px-3 py-2 text-left text-sm text-muted-foreground hover:bg-muted/35 hover:text-foreground"
              type="button"
              onclick={() => context.openObject(entry.object)}
            >
              <span class="block truncate text-foreground">
                {entry.object.title}
              </span>
            </button>
          {:else}
            <p
              class="rounded-lg border border-dashed border-border px-3 py-4 text-sm text-muted-foreground"
            >
              Hypotheses, open questions, and research directions will live
              here.
            </p>
          {/each}
        </div>
      </section>

      {#if concepts.length}
        <section>
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <Brain size={16} class={entityMeta.concept.text} />
              <h4 class="text-sm font-semibold text-foreground">
                Useful Concepts
              </h4>
            </div>
            <span class="text-xs text-muted-foreground">{concepts.length}</span>
          </div>
          <div class="mt-3 flex flex-wrap gap-2">
            {#each concepts.slice(0, 10) as entry}
              <button
                class="rounded-md border border-border bg-muted/[0.06] px-2 py-1 text-xs text-muted-foreground hover:bg-muted/35 hover:text-foreground"
                type="button"
                onclick={() => context.openObject(entry.object)}
              >
                {entry.object.title}
              </button>
            {/each}
          </div>
        </section>
      {/if}

      {#if reviews.length}
        <section>
          <div class="flex items-center gap-2">
            <PenLine size={16} class={entityMeta.review.text} />
            <h4 class="text-sm font-semibold text-foreground">Reviews</h4>
          </div>
          <div class="mt-3 grid gap-2">
            {#each reviews.slice(0, 4) as entry}
              <button
                class="rounded-md border border-border bg-muted/[0.06] px-3 py-2 text-left text-sm text-muted-foreground hover:bg-muted/35 hover:text-foreground"
                type="button"
                onclick={() => context.openObject(entry.object)}
              >
                <span class="block truncate text-foreground">
                  {entry.object.title}
                </span>
              </button>
            {/each}
          </div>
        </section>
      {/if}
    </aside>
  </div>

  <section bind:this={briefSection} class="scroll-mt-5 border-t border-border">
    <div
      class="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 px-6 py-3"
    >
      <div class="flex items-center gap-2">
        <FileText size={15} class="text-muted-foreground" />
        <h4 class="text-sm font-semibold text-foreground">Project Brief</h4>
      </div>
      <div
        class="flex items-center gap-1 rounded-md border border-border bg-muted/15 p-1"
        aria-label="Project note mode"
      >
        <button
          class={noteMode === 'reading'
            ? 'h-7 rounded bg-background px-2.5 text-xs font-medium text-foreground shadow-sm'
            : 'h-7 rounded px-2.5 text-xs text-muted-foreground transition hover:text-foreground'}
          type="button"
          onclick={() => (noteMode = 'reading')}
        >
          Reading
        </button>
        <button
          class={noteMode === 'editing'
            ? 'h-7 rounded bg-background px-2.5 text-xs font-medium text-foreground shadow-sm'
            : 'h-7 rounded px-2.5 text-xs text-muted-foreground transition hover:text-foreground'}
          type="button"
          onclick={() => (noteMode = 'editing')}
        >
          Editing
        </button>
      </div>
    </div>

    <div class="min-h-[420px]">
      {#if noteMode === 'reading'}
        <MarkdownPreview
          content={context.content}
          objectTitle={context.object.title}
          compact
          showMetadata={false}
        />
      {:else}
        <div class="h-[520px]">
          <MarkdownPanel {context} />
        </div>
      {/if}
    </div>
  </section>
</section>
