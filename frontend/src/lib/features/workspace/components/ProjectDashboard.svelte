<script lang="ts">
  import {
    BookOpen,
    Boxes,
    Brain,
    FileText,
    GitBranch,
    Lightbulb,
    Network,
    PenLine
  } from '@lucide/svelte';
  import { onMount } from 'svelte';

  import { entityMeta } from '$lib/design/entities';
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
    listWorkspaceNotes,
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

  const metadataKeys = ['status', 'priority', 'domain', 'method', 'tags'];

  let { context }: Props = $props();
  let noteMode = $state<'reading' | 'editing'>('reading');
  let projectNotes = $state<ProjectNotePreview[]>([]);
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
      projectNotes.length
    );
  }

  async function loadProjectNotes(): Promise<void> {
    const previews: ProjectNotePreview[] = [];
    for (const entry of papers.slice(0, 8)) {
      const response = await listWorkspaceNotes(entry.object.id).catch(
        () => null
      );
      if (!response) continue;
      for (const note of response.notes.slice(0, 3)) {
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

  onMount(() => {
    void loadProjectNotes();
  });

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
  let visibleReading = $derived(
    continueReading.length ? continueReading : papers.slice(0, 4)
  );
  let isolatedPapers = $derived(
    papers.filter((entry) => !entry.roles.length).length
  );
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
      <span
        class="rounded-md border border-border bg-muted/20 px-2 py-1 text-xs text-muted-foreground"
      >
        {papers.length} papers
      </span>
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

  <ProjectBrainHub
    paperCount={papers.length}
    noteCount={projectNotes.length}
    conceptCount={concepts.length}
    ideaCount={researchIdeas.length}
    reviewCount={reviews.length}
    relationCount={relationCount()}
    onSelect={focusSection}
  />

  <div
    class="grid gap-5 px-6 py-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.9fr)]"
  >
    <div class="grid gap-5">
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

        <div class="mt-3 grid gap-3 md:grid-cols-2">
          {#each visibleReading as entry}
            <button
              class="min-h-24 rounded-lg border border-border bg-muted/[0.06] px-3 py-3 text-left transition hover:bg-muted/35"
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
            {projectNotes.length}
          </span>
        </div>

        <div class="mt-3 grid gap-2 md:grid-cols-2">
          {#each projectNotes as preview}
            <button
              class="rounded-lg border border-entity-note/20 bg-entity-note/[0.05] px-3 py-2 text-left hover:bg-entity-note/10"
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
          {:else}
            <p
              class="rounded-lg border border-dashed border-border px-3 py-5 text-sm text-muted-foreground"
            >
              Reading notes from project papers will appear here.
            </p>
          {/each}
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
              {projectNotes.length}
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

    <aside class="grid content-start gap-5">
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
