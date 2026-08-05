<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import {
    BrainCircuit,
    ChevronRight,
    FolderKanban,
    LoaderCircle,
    Settings2
  } from '@lucide/svelte';
  import { onMount } from 'svelte';

  import ProjectAssistantPanel from '$lib/features/assistant/components/ProjectAssistantPanel.svelte';
  import { citationWorkspaceUrl } from '$lib/features/assistant/services/assistantNavigation';
  import type { AssistantCitation } from '$lib/features/assistant/types/assistant';
  import type { LinkableObject } from '$lib/features/linking/types/linking';
  import { listProjects } from '$lib/features/workspace/services/workspaceApi';

  let projects = $state<LinkableObject[]>([]);
  let selectedProjectId = $state('');
  let loading = $state(true);
  let error = $state<string | null>(null);

  let selectedProject = $derived(
    projects.find((project) => project.id === selectedProjectId) ?? null
  );

  onMount(() => {
    void loadProjects();
  });

  async function loadProjects(): Promise<void> {
    loading = true;
    error = null;
    try {
      projects = await listProjects();
      const requestedProject = $page.url.searchParams.get('project');
      selectedProjectId =
        projects.find((project) => project.id === requestedProject)?.id ??
        projects[0]?.id ??
        '';
    } catch (loadError) {
      error =
        loadError instanceof Error
          ? loadError.message
          : 'Unable to load projects.';
    } finally {
      loading = false;
    }
  }

  function selectProject(projectId: string): void {
    selectedProjectId = projectId;
    void goto(`/assistant?project=${encodeURIComponent(projectId)}`, {
      replaceState: true,
      noScroll: true,
      keepFocus: true
    });
  }

  async function openCitation(citation: AssistantCitation): Promise<void> {
    if (!selectedProject) return;
    await goto(citationWorkspaceUrl(selectedProject.id, citation));
  }
</script>

<section class="flex h-[calc(100vh-4rem)] min-h-0 flex-col bg-background">
  <header
    class="flex shrink-0 flex-wrap items-center justify-between gap-4 border-b border-border bg-surface/60 px-4 py-4 sm:px-6"
  >
    <div class="flex min-w-0 items-center gap-3">
      <span
        class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-accent/40 bg-accent/10 text-accent"
      >
        <BrainCircuit size={19} />
      </span>
      <div class="min-w-0">
        <h1 class="truncate text-base font-semibold text-foreground">
          Local Research Assistant
        </h1>
        <p class="mt-0.5 truncate text-xs text-muted-foreground">
          Ollama local · selected project sources only
        </p>
      </div>
    </div>

    <div class="flex min-w-0 items-center gap-2">
      {#if projects.length}
        <label class="sr-only" for="assistant-project">Project</label>
        <select
          id="assistant-project"
          class="h-9 min-w-0 max-w-52 rounded-md border border-border bg-background px-2 text-xs text-foreground outline-none focus:border-accent/50 lg:hidden"
          value={selectedProjectId}
          onchange={(event) =>
            selectProject((event.currentTarget as HTMLSelectElement).value)}
        >
          {#each projects as project}
            <option value={project.id}>{project.title}</option>
          {/each}
        </select>
      {/if}
      <a
        href="/settings/ai"
        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-border bg-background text-muted-foreground transition hover:border-accent/40 hover:text-foreground"
        aria-label="Local AI settings"
        title="Local AI settings"
      >
        <Settings2 size={15} />
      </a>
    </div>
  </header>

  <div class="grid min-h-0 flex-1 lg:grid-cols-[252px_minmax(0,1fr)]">
    <aside
      class="hidden min-h-0 border-r border-border bg-surface/30 lg:flex lg:flex-col"
      aria-label="Project selection"
    >
      <div class="border-b border-border px-4 py-3">
        <p class="text-[0.68rem] font-medium uppercase text-muted-foreground">
          Research projects
        </p>
        <p class="mt-1 text-xs text-muted-foreground">
          {projects.length} available
        </p>
      </div>
      <div class="min-h-0 flex-1 overflow-y-auto p-2">
        {#each projects as project}
          <button
            type="button"
            class={selectedProjectId === project.id
              ? 'flex w-full items-center gap-2.5 border-l-2 border-accent bg-accent/[0.08] px-3 py-2.5 text-left text-foreground'
              : 'flex w-full items-center gap-2.5 border-l-2 border-transparent px-3 py-2.5 text-left text-muted-foreground transition hover:bg-muted/35 hover:text-foreground'}
            aria-pressed={selectedProjectId === project.id}
            onclick={() => selectProject(project.id)}
          >
            <FolderKanban size={15} class="shrink-0 text-entity-project" />
            <span class="min-w-0 flex-1 truncate text-sm font-medium">
              {project.title}
            </span>
            <ChevronRight size={13} class="shrink-0" />
          </button>
        {/each}
      </div>
      <div
        class="border-t border-border px-4 py-3 text-xs leading-5 text-muted-foreground"
      >
        Answers are generated from the selected project's indexed notes and
        PDFs.
      </div>
    </aside>

    <main class="min-h-0 overflow-hidden">
      {#if loading}
        <div
          class="flex h-full items-center justify-center text-muted-foreground"
        >
          <LoaderCircle size={19} class="animate-spin" />
        </div>
      {:else if error}
        <div class="flex h-full items-center justify-center px-6 text-center">
          <div>
            <p class="text-sm font-medium text-foreground">
              Unable to open the assistant
            </p>
            <p class="mt-2 text-xs text-entity-review">{error}</p>
          </div>
        </div>
      {:else if selectedProject}
        <ProjectAssistantPanel
          project={selectedProject}
          {openCitation}
          refreshProject={loadProjects}
          variant="workspace"
        />
      {:else}
        <div class="flex h-full items-center justify-center px-6 text-center">
          <div>
            <FolderKanban size={24} class="mx-auto text-muted-foreground" />
            <p class="mt-3 text-sm font-medium text-foreground">
              No research project yet
            </p>
            <p class="mt-1 text-xs text-muted-foreground">
              Create a project in the Workspace before starting a conversation.
            </p>
            <a
              href="/workspace"
              class="mt-4 inline-flex h-9 items-center rounded-md bg-accent px-3 text-xs font-semibold text-accent-foreground"
            >
              Open Workspace
            </a>
          </div>
        </div>
      {/if}
    </main>
  </div>
</section>
