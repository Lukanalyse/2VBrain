<script lang="ts">
  import {
    BookOpen,
    CheckCircle2,
    FileText,
    FolderKanban,
    Search,
    Sparkles
  } from '@lucide/svelte';
  import { createEventDispatcher, onMount } from 'svelte';

  import type { LinkableObject } from '$lib/features/linking/types/linking';
  import type { PdfMetadataPreview } from '$lib/features/library/types/library';
  import {
    createProject,
    listProjects
  } from '$lib/features/workspace/services/workspaceApi';

  export let metadata: PdfMetadataPreview;
  export let filename: string;
  export let isImporting = false;

  const dispatch = createEventDispatcher<{
    import: PdfMetadataPreview;
    cancel: void;
  }>();

  let draft: PdfMetadataPreview = { ...metadata };
  let projects: LinkableObject[] = [];
  let projectQuery = '';
  let newProjectTitle = '';
  let creatingProject = false;

  $: visibleProjects = projects
    .filter((project) =>
      project.title.toLowerCase().includes(projectQuery.trim().toLowerCase())
    )
    .slice(0, 6);
  $: selectedProject = projects.find(
    (project) => project.id === draft.project_id
  );
  $: paperTitle = draft.title.trim() || filename.replace(/\.pdf$/i, '');
  $: sourceLabel = draft.metadata_source || 'pdf';
  $: confidenceLabel = draft.metadata_confidence || 'low';
  $: importDisabled = isImporting || !draft.project_id;
  $: primaryActionLabel = selectedProject
    ? `Import to ${selectedProject.title}`
    : 'Choose a Project';

  onMount(async () => {
    projects = await listProjects().catch(() => []);
  });

  async function createAndSelectProject(): Promise<void> {
    const title = newProjectTitle.trim();
    if (!title) return;
    creatingProject = true;
    try {
      const created = (await createProject(title)).object;
      projects = [created, ...projects];
      draft.project_id = created.id;
      newProjectTitle = '';
      projectQuery = '';
    } finally {
      creatingProject = false;
    }
  }
</script>

<div
  class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 backdrop-blur-sm"
>
  <section
    class="max-h-[90vh] w-full max-w-4xl overflow-auto rounded-lg border border-border bg-background shadow-panel"
  >
    <div class="border-b border-border px-5 py-4">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div class="min-w-0">
          <p
            class="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground"
          >
            Import Paper
          </p>
          <h2 class="mt-2 truncate text-lg font-semibold text-foreground">
            {paperTitle}
          </h2>
          <p class="mt-1 truncate text-xs text-muted-foreground">{filename}</p>
        </div>
        <span
          class="inline-flex h-7 items-center gap-1.5 rounded-md border border-border bg-muted/20 px-2 text-xs text-muted-foreground"
        >
          <Sparkles size={12} />
          {sourceLabel} · {confidenceLabel}
        </span>
      </div>
    </div>

    <div class="grid gap-5 p-5 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div class="space-y-4">
        <section class="rounded-lg border border-border bg-muted/[0.06] p-4">
          <div class="flex items-start gap-3">
            <div
              class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border bg-background/60 text-accent"
            >
              <CheckCircle2 size={16} />
            </div>
            <div class="min-w-0">
              <p class="text-sm font-medium text-foreground">
                Metadata detected
              </p>
              <p class="mt-1 text-sm leading-6 text-muted-foreground">
                Research OS will create the Paper and its Reading Note from this
                import.
              </p>
            </div>
          </div>

          <div class="mt-4 grid gap-3 sm:grid-cols-3">
            <div
              class="min-w-0 rounded-md border border-border bg-background/45 p-3"
            >
              <p class="text-[11px] uppercase text-muted-foreground">DOI</p>
              <p class="mt-1 truncate text-sm text-foreground">
                {draft.doi || 'Not found'}
              </p>
            </div>
            <div
              class="min-w-0 rounded-md border border-border bg-background/45 p-3"
            >
              <p class="text-[11px] uppercase text-muted-foreground">Year</p>
              <p class="mt-1 truncate text-sm text-foreground">
                {draft.year ?? 'Unknown'}
              </p>
            </div>
            <div
              class="min-w-0 rounded-md border border-border bg-background/45 p-3"
            >
              <p class="text-[11px] uppercase text-muted-foreground">Source</p>
              <p class="mt-1 truncate text-sm text-foreground">
                {sourceLabel}
              </p>
            </div>
          </div>
        </section>

        <details class="rounded-lg border border-border bg-muted/[0.06] p-4">
          <summary
            class="cursor-pointer text-xs font-medium uppercase text-muted-foreground"
          >
            Bibliographic Metadata
          </summary>
          <div class="mt-4 grid gap-4 md:grid-cols-2">
            <label class="block md:col-span-2">
              <span class="text-sm font-medium text-foreground">Title</span>
              <input
                bind:value={draft.title}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
              />
            </label>
            <label class="block">
              <span class="text-sm font-medium text-foreground">Authors</span>
              <input
                bind:value={draft.authors}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
              />
            </label>
            <label class="block">
              <span class="text-sm font-medium text-foreground">Year</span>
              <input
                value={draft.year ?? ''}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
                type="number"
                on:input={(event) => {
                  const value = event.currentTarget.value;
                  draft.year = value ? Number(value) : null;
                }}
              />
            </label>
            <label class="block">
              <span class="text-sm font-medium text-foreground">Journal</span>
              <input
                bind:value={draft.journal}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
              />
            </label>
            <label class="block">
              <span class="text-sm font-medium text-foreground">Conference</span
              >
              <input
                bind:value={draft.conference}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
              />
            </label>
            <label class="block">
              <span class="text-sm font-medium text-foreground">DOI</span>
              <input
                bind:value={draft.doi}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
              />
            </label>
            <label class="block">
              <span class="text-sm font-medium text-foreground">Publisher</span>
              <input
                bind:value={draft.publisher}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
              />
            </label>
            <label class="block md:col-span-2">
              <span class="text-sm font-medium text-foreground">Keywords</span>
              <input
                bind:value={draft.keywords}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
              />
            </label>
            <label class="block md:col-span-2">
              <span class="text-sm font-medium text-foreground">Abstract</span>
              <textarea
                bind:value={draft.abstract}
                class="mt-2 min-h-32 w-full resize-y rounded-md border border-border bg-background/50 px-3 py-2 text-sm outline-none focus:border-accent/50"
              ></textarea>
            </label>
          </div>
        </details>

        <details class="rounded-lg border border-border bg-muted/[0.06] p-4">
          <summary
            class="cursor-pointer text-xs font-medium uppercase text-muted-foreground"
          >
            Research Metadata
          </summary>
          <div class="mt-4 grid gap-4 md:grid-cols-2">
            <label class="block">
              <span class="text-sm font-medium text-foreground"
                >Reading Status</span
              >
              <select
                bind:value={draft.reading_status}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
              >
                <option value="unread">Unread</option>
                <option value="reading">Reading</option>
                <option value="reviewed">Reviewed</option>
                <option value="mastered">Mastered</option>
              </select>
            </label>
            <label class="block">
              <span class="text-sm font-medium text-foreground">Progress</span>
              <input
                bind:value={draft.reading_progress}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
                max="100"
                min="0"
                type="number"
              />
            </label>
            <label class="block">
              <span class="text-sm font-medium text-foreground">Importance</span
              >
              <input
                bind:value={draft.importance}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
                placeholder="high, medium, low"
              />
            </label>
            <label class="block">
              <span class="text-sm font-medium text-foreground">Priority</span>
              <input
                bind:value={draft.priority}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
              />
            </label>
            <label class="block">
              <span class="text-sm font-medium text-foreground">Domain</span>
              <input
                bind:value={draft.domain}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
              />
            </label>
            <label class="block">
              <span class="text-sm font-medium text-foreground">Method</span>
              <input
                bind:value={draft.method}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
              />
            </label>
            <label class="block">
              <span class="text-sm font-medium text-foreground">Difficulty</span
              >
              <input
                bind:value={draft.difficulty}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
              />
            </label>
            <label class="block">
              <span class="text-sm font-medium text-foreground"
                >Personal Tags</span
              >
              <input
                bind:value={draft.personal_tags}
                class="mt-2 h-10 w-full rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
                placeholder="comma separated"
              />
            </label>
          </div>
        </details>
      </div>

      <aside class="space-y-4">
        <section class="rounded-lg border border-border bg-muted/[0.06] p-4">
          <div class="flex items-start gap-3">
            <div
              class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border bg-background/60 text-accent"
            >
              <FolderKanban size={16} />
            </div>
            <div>
              <p class="text-sm font-medium text-foreground">Project</p>
              <p class="mt-1 text-sm leading-6 text-muted-foreground">
                Choose where this Paper belongs.
              </p>
            </div>
          </div>

          {#if selectedProject}
            <div
              class="mt-4 flex items-center justify-between gap-3 rounded-md border border-accent/35 bg-accent/10 px-3 py-2"
            >
              <span
                class="min-w-0 truncate text-sm font-medium text-foreground"
              >
                {selectedProject.title}
              </span>
              <button
                class="text-xs text-muted-foreground hover:text-foreground"
                type="button"
                on:click={() => (draft.project_id = '')}
              >
                Change
              </button>
            </div>
          {:else}
            <label
              class="mt-4 flex h-10 items-center gap-2 rounded-md border border-border bg-background/50 px-3 text-sm text-muted-foreground focus-within:border-accent/50"
            >
              <Search size={14} />
              <input
                bind:value={projectQuery}
                class="min-w-0 flex-1 bg-transparent text-foreground outline-none"
                placeholder="Find a project"
              />
            </label>

            <div
              class="mt-2 max-h-44 overflow-auto rounded-md border border-border bg-background/30 p-1"
            >
              {#each visibleProjects as project}
                <button
                  class="flex w-full items-center rounded-md px-2 py-2 text-left text-sm text-muted-foreground hover:bg-muted/45 hover:text-foreground"
                  type="button"
                  on:click={() => {
                    draft.project_id = project.id;
                    projectQuery = '';
                  }}
                >
                  <span class="min-w-0 truncate">{project.title}</span>
                </button>
              {:else}
                <p class="px-2 py-2 text-xs text-muted-foreground">
                  No matching project.
                </p>
              {/each}
            </div>
            <p class="mt-2 text-xs text-muted-foreground">
              A Paper needs one Project. Create one below if needed.
            </p>

            <div class="mt-3 flex gap-2">
              <input
                bind:value={newProjectTitle}
                class="h-9 min-w-0 flex-1 rounded-md border border-border bg-background/50 px-3 text-sm outline-none focus:border-accent/50"
                placeholder="Create new project"
                on:keydown={(event) =>
                  event.key === 'Enter' && createAndSelectProject()}
              />
              <button
                class="h-9 rounded-md border border-border bg-muted/25 px-3 text-xs text-muted-foreground hover:text-foreground disabled:opacity-50"
                type="button"
                disabled={!newProjectTitle.trim() || creatingProject}
                on:click={createAndSelectProject}
              >
                Create
              </button>
            </div>
          {/if}
        </section>

        <section class="rounded-lg border border-border bg-muted/[0.06] p-4">
          <div class="grid gap-3">
            <div class="flex items-start gap-3">
              <FileText
                size={16}
                class="mt-0.5 shrink-0 text-muted-foreground"
              />
              <div>
                <p class="text-sm font-medium text-foreground">Paper</p>
                <p class="text-xs text-muted-foreground">
                  Bibliographic record and PDF stored in the vault.
                </p>
              </div>
            </div>
            <div class="flex items-start gap-3">
              <BookOpen
                size={16}
                class="mt-0.5 shrink-0 text-muted-foreground"
              />
              <div>
                <p class="text-sm font-medium text-foreground">Reading Note</p>
                <p class="text-xs text-muted-foreground">
                  Created automatically beside the Paper.
                </p>
              </div>
            </div>
          </div>
        </section>
      </aside>
    </div>

    <div
      class="flex flex-wrap items-center justify-between gap-3 border-t border-border px-5 py-4"
    >
      <p class="text-xs text-muted-foreground">
        {selectedProject
          ? 'Ready to import.'
          : 'Choose or create a Project to continue.'}
      </p>
      <div class="flex gap-2">
        <button
          class="h-10 rounded-md border border-border bg-muted/25 px-4 text-sm text-muted-foreground hover:text-foreground"
          type="button"
          on:click={() => dispatch('cancel')}
        >
          Cancel
        </button>
        <button
          class="h-10 rounded-md bg-accent px-4 text-sm font-medium text-accent-foreground hover:bg-accent/90 disabled:opacity-60"
          type="button"
          disabled={importDisabled}
          on:click={() => dispatch('import', draft)}
        >
          {primaryActionLabel}
        </button>
      </div>
    </div>
  </section>
</div>
