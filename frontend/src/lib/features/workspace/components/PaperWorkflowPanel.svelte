<script lang="ts">
  import { FileText, Link2, Plus, Search } from '@lucide/svelte';
  import { onDestroy, onMount } from 'svelte';

  import TagBadges from '$lib/components/ui/TagBadges.svelte';
  import TagEditor from '$lib/components/ui/TagEditor.svelte';
  import { entityMeta } from '$lib/design/entities';
  import type { LinkableObject } from '$lib/features/linking/types/linking';
  import RelationRow from '$lib/features/workspace/components/RelationRow.svelte';
  import {
    createProject,
    listProjects,
    setObjectTags,
    setWorkspaceProject,
    updateWorkspaceResearchMetadata
  } from '$lib/features/workspace/services/workspaceApi';
  import type {
    ReadingStatus,
    WorkspaceResearchMetadata
  } from '$lib/features/workspace/services/workspaceApi';
  import type { WorkspacePanelContext } from '$lib/features/workspace/types/panels';

  type Props = {
    context: WorkspacePanelContext;
  };

  let { context }: Props = $props();

  const PaperIcon = entityMeta.paper.icon;
  const ProjectIcon = entityMeta.project.icon;

  let objectMetadata = $derived(context.detail?.metadata ?? {});

  function fmtDate(value: string | undefined): string {
    if (!value) return '—';
    const date = new Date(value.trim());
    if (Number.isNaN(date.getTime())) return value.trim();
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  let projects = $state<LinkableObject[]>([]);
  let metadataKey = $state('');
  let metadataDraft = $state<WorkspaceResearchMetadata>({
    status: 'unread',
    reading_progress: 0,
    importance: '',
    priority: '',
    domain: '',
    method: '',
    difficulty: '',
    personal_tags: ''
  });
  let projectQuery = $state('');
  let paperQuery = $state('');
  let paperResults = $state<LinkableObject[]>([]);
  let newProjectTitle = $state('');
  let advancedTitle = $state('');
  let advancedKind = $state<'concept' | 'brainstorm' | 'review'>('concept');
  let busy = $state('');
  let message = $state<string | null>(null);
  let paperSearchTimer: ReturnType<typeof setTimeout> | null = null;
  let paperSearchRequest = 0;

  let linkedProjects = $derived(
    unique([
      ...(context.detail?.related.project ?? []),
      ...(context.detail?.backlinks.project ?? [])
    ]).filter(
      (project) =>
        !context.object.project_id || project.id === context.object.project_id
    )
  );
  let currentProject = $derived(
    context.object.project_id
      ? projects.find((project) => project.id === context.object.project_id)
      : null
  );
  let visibleLinkedProjects = $derived(
    unique([...(currentProject ? [currentProject] : []), ...linkedProjects])
  );
  let linkedPapers = $derived(
    unique([
      ...(context.detail?.related.paper ?? []),
      ...(context.detail?.backlinks.paper ?? [])
    ]).filter((item) => item.id !== context.object.id)
  );
  let visibleProjects = $derived(
    projects
      .filter((project) =>
        project.title.toLowerCase().includes(projectQuery.trim().toLowerCase())
      )
      .slice(0, 5)
  );
  let readingNotes = $derived(context.notes ?? []);

  onMount(async () => {
    projects = await listProjects().catch(() => []);
  });

  $effect(() => {
    const key = JSON.stringify({
      id: context.object.id,
      metadata: context.detail?.metadata ?? {}
    });
    if (key === metadataKey) return;
    metadataKey = key;
    metadataDraft = metadataFromContext();
  });

  function unique(items: LinkableObject[]): LinkableObject[] {
    const seen = new Set<string>();
    return items.filter((item) => {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });
  }

  function metadataText(key: string): string {
    return (context.detail?.metadata?.[key] ?? '')
      .trim()
      .replace(/^\[(.*)\]$/, '$1');
  }

  function metadataFromContext(): WorkspaceResearchMetadata {
    const status = metadataText('status').toLowerCase();
    const readingStatus: ReadingStatus =
      status === 'reading' ||
      status === 'paused' ||
      status === 'reviewed' ||
      status === 'mastered'
        ? status
        : 'unread';
    const progress = Number(metadataText('reading_progress') || 0);

    return {
      status: readingStatus,
      reading_progress: Number.isFinite(progress)
        ? Math.min(100, Math.max(0, progress))
        : 0,
      importance: metadataText('importance'),
      priority: metadataText('priority'),
      domain: metadataText('domain'),
      method: metadataText('method'),
      difficulty: metadataText('difficulty'),
      personal_tags: metadataText('tags') || metadataText('personal_tags')
    };
  }

  async function run(name: string, action: () => Promise<void>): Promise<void> {
    busy = name;
    message = null;
    try {
      await action();
      message = 'Updated.';
    } catch (error) {
      message = error instanceof Error ? error.message : 'Action failed.';
    } finally {
      busy = '';
    }
  }

  async function assignProject(project: LinkableObject): Promise<void> {
    await run(`project-${project.id}`, async () => {
      await setWorkspaceProject(context.object.id, project.id);
      await context.refreshObject();
      projects = await listProjects().catch(() => projects);
      projectQuery = '';
    });
  }

  async function createAndAssignProject(): Promise<void> {
    const title = newProjectTitle.trim();
    if (!title) return;
    await run('new-project', async () => {
      const created = (await createProject(title)).object;
      await setWorkspaceProject(context.object.id, created.id);
      await context.refreshObject();
      projects = await listProjects().catch(() => projects);
      newProjectTitle = '';
      projectQuery = '';
    });
  }

  function schedulePaperSearch(): void {
    if (paperSearchTimer) clearTimeout(paperSearchTimer);
    const request = ++paperSearchRequest;
    const query = paperQuery.trim();
    paperSearchTimer = setTimeout(async () => {
      const results = query
        ? (await context.searchObjects(query)).filter(
            (item) => item.type === 'paper' && item.id !== context.object.id
          )
        : [];
      if (request === paperSearchRequest) paperResults = results;
    }, 170);
  }

  onDestroy(() => {
    if (paperSearchTimer) clearTimeout(paperSearchTimer);
    paperSearchRequest += 1;
  });

  async function linkPaper(paper: LinkableObject): Promise<void> {
    await run(`paper-${paper.id}`, async () => {
      await context.linkObjectToTarget(paper);
      await context.refreshObject();
      paperQuery = '';
      paperResults = [];
    });
  }

  async function runAdvanced(): Promise<void> {
    const title = advancedTitle.trim();
    if (!title) return;
    await run(advancedKind, async () => {
      if (advancedKind === 'concept')
        await context.createConceptFromTitle(title);
      if (advancedKind === 'brainstorm')
        await context.createBrainstormFromTitle(title);
      if (advancedKind === 'review') await context.createReviewFromTitle(title);
      advancedTitle = '';
    });
  }

  async function saveTags(next: string[]): Promise<void> {
    await setObjectTags(context.object.id, next);
    await context.refreshObject();
  }

  async function saveResearchMetadata(): Promise<void> {
    await run('metadata', async () => {
      await updateWorkspaceResearchMetadata(context.object.id, {
        ...metadataDraft,
        reading_progress: Math.min(
          100,
          Math.max(0, Number(metadataDraft.reading_progress) || 0)
        )
      });
      await context.refreshObject();
    });
  }
</script>

<aside
  class="right-panel flex min-w-0 flex-col gap-5 overflow-x-hidden overflow-y-auto border-l border-border bg-background/70 px-5 py-5"
>
  <!-- OBJECT -->
  <header class="flex items-start gap-2.5">
    <span
      class={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md border ${entityMeta.paper.border} ${entityMeta.paper.tint}`}
    >
      <PaperIcon size={16} class={entityMeta.paper.text} />
    </span>
    <div class="min-w-0 flex-1">
      <p class="text-[0.7rem] font-semibold uppercase tracking-[0.08em] text-accent">
        Paper
      </p>
      <h2 class="text-base font-semibold leading-tight text-foreground">
        {context.object.title}
      </h2>
      <TagBadges tags={context.detail?.tags} class="mt-1.5" />
    </div>
  </header>

  {#if message}
    <p
      class="rounded-md border border-border bg-muted/[0.08] px-3 py-2 text-xs text-muted-foreground"
    >
      {message}
    </p>
  {/if}

  <!-- ACTIONS -->
  <section class="border-t border-border pt-4">
    <p class="ros-section-label"><ProjectIcon size={13} /> Project</p>

    <div class="mt-3 grid gap-1.5">
      {#each visibleLinkedProjects as project}
        <RelationRow object={project} onclick={() => context.openObject(project)} />
      {:else}
        <p
          class={`rounded-md border border-dashed px-3 py-2 text-xs text-muted-foreground ${entityMeta.project.border} ${entityMeta.project.tint}`}
        >
          No project assigned.
        </p>
      {/each}
    </div>

    <label class="ros-input-affix mt-2.5">
      <Search size={14} />
      <input
        bind:value={projectQuery}
        class="min-w-0 flex-1 bg-transparent text-foreground outline-none placeholder:text-muted-foreground"
        placeholder="Choose project"
      />
    </label>

    {#if projectQuery.trim()}
      <div class="mt-2 grid max-h-40 gap-1.5 overflow-auto">
        {#each visibleProjects as project}
          <RelationRow object={project} onclick={() => assignProject(project)}>
            {#snippet trailing()}
              <Plus size={13} />
            {/snippet}
          </RelationRow>
        {:else}
          <p class="px-1 py-1 text-xs text-muted-foreground">
            No matching project.
          </p>
        {/each}
      </div>
    {/if}

    <div class="mt-2 flex gap-2">
      <input
        bind:value={newProjectTitle}
        class="ros-input"
        placeholder="New project"
        onkeydown={(event) => event.key === 'Enter' && createAndAssignProject()}
      />
      <button
        class="ros-btn-icon"
        type="button"
        aria-label="Create project"
        disabled={!newProjectTitle.trim() || busy === 'new-project'}
        onclick={createAndAssignProject}
      >
        <Plus size={15} />
      </button>
    </div>

    <div class="mt-3 flex gap-2">
      <input
        bind:value={advancedTitle}
        class="ros-input"
        placeholder={advancedKind === 'brainstorm' ? 'Research idea' : 'Title'}
        onkeydown={(event) => event.key === 'Enter' && runAdvanced()}
      />
      <div
        class="flex shrink-0 gap-1 rounded-md border border-border bg-background p-1"
      >
        {#each ['concept', 'brainstorm', 'review'] as kind}
          {@const KindIcon = entityMeta[kind as 'concept' | 'brainstorm' | 'review'].icon}
          <button
            class={advancedKind === kind
              ? `flex h-7 w-7 items-center justify-center rounded bg-muted ${entityMeta[kind as 'concept' | 'brainstorm' | 'review'].text}`
              : 'flex h-7 w-7 items-center justify-center rounded text-muted-foreground hover:text-foreground'}
            type="button"
            title={kind === 'brainstorm' ? 'Research idea' : kind}
            onclick={() =>
              (advancedKind = kind as 'concept' | 'brainstorm' | 'review')}
          >
            <KindIcon size={14} />
          </button>
        {/each}
      </div>
      <button
        class="ros-btn-icon"
        type="button"
        aria-label="Create contextual object"
        disabled={!advancedTitle.trim() || busy === advancedKind}
        onclick={runAdvanced}
      >
        <Plus size={15} />
      </button>
    </div>
  </section>

  <!-- QUICK LINKS -->
  <section class="border-t border-border pt-4">
    <p class="ros-section-label"><Link2 size={13} /> Quick Links</p>
    <label class="ros-input-affix mt-3">
      <Search size={14} />
      <input
        bind:value={paperQuery}
        class="min-w-0 flex-1 bg-transparent text-foreground outline-none placeholder:text-muted-foreground"
        placeholder="Link an existing paper"
        oninput={schedulePaperSearch}
      />
    </label>
    {#if paperResults.length}
      <div class="mt-2 grid max-h-44 gap-1.5 overflow-auto">
        {#each paperResults.slice(0, 6) as paper}
          <RelationRow object={paper} onclick={() => linkPaper(paper)}>
            {#snippet trailing()}
              <Plus size={13} />
            {/snippet}
          </RelationRow>
        {/each}
      </div>
    {/if}
  </section>

  <!-- RELATIONS -->
  <section class="border-t border-border pt-4">
    <p class="ros-section-label">Relations</p>
    <div class="mt-3 grid gap-1.5">
      {#each linkedPapers.slice(0, 6) as paper}
        <RelationRow object={paper} onclick={() => context.openObject(paper)} />
      {:else}
        <p class="text-xs text-muted-foreground">No linked object yet.</p>
      {/each}
    </div>

    {#if readingNotes.length}
      <p class="ros-section-label mt-4">
        <FileText size={13} class="text-entity-note" /> Reading Notes
      </p>
      <div class="mt-2 grid gap-1">
        {#each readingNotes.slice(0, 5) as note}
          <div
            class="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs text-muted-foreground"
          >
            <FileText size={13} class="text-entity-note" />
            <span class="min-w-0 truncate">{note.title}</span>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  <!-- METADATA -->
  <section class="border-t border-border pt-4">
    <div class="flex items-center justify-between gap-3">
      <p class="ros-section-label">Metadata</p>
      <button
        class="ros-btn-ghost"
        type="button"
        disabled={busy === 'metadata'}
        onclick={saveResearchMetadata}
      >
        Save
      </button>
    </div>

    <div class="mt-3 grid gap-3">
      <label class="grid gap-1">
        <span class="text-xs text-muted-foreground">Reading Status</span>
        <select bind:value={metadataDraft.status} class="ros-input">
          <option value="unread">Unread</option>
          <option value="reading">Reading</option>
          <option value="paused">Paused</option>
          <option value="reviewed">Reviewed</option>
          <option value="mastered">Mastered</option>
        </select>
      </label>

      <label class="grid gap-1">
        <span class="text-xs text-muted-foreground">Domain</span>
        <input
          bind:value={metadataDraft.domain}
          class="ros-input"
          placeholder="e.g. bandits, causal inference"
        />
      </label>

      <div class="grid gap-1">
        <span class="text-xs text-muted-foreground">Tags</span>
        <TagEditor tags={context.detail?.tags} onSave={saveTags} />
      </div>

      <div class="mt-1 grid gap-2 border-t border-border/60 pt-3">
        <div class="flex items-baseline justify-between gap-3">
          <span class="text-xs text-muted-foreground">Created</span>
          <span class="text-xs text-foreground">{fmtDate(objectMetadata.created)}</span>
        </div>
        <div class="flex items-baseline justify-between gap-3">
          <span class="text-xs text-muted-foreground">Modified</span>
          <span class="text-xs text-foreground">{fmtDate(objectMetadata.updated)}</span>
        </div>
      </div>
    </div>
  </section>
</aside>
