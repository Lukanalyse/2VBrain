<script lang="ts">
  import {
    BookOpen,
    ExternalLink,
    FileText,
    Lightbulb,
    PenLine,
    StickyNote
  } from '@lucide/svelte';

  import { entityMeta } from '$lib/design/entities';
  import MarkdownPreview from '$lib/features/research-workspace/MarkdownPreview.svelte';
  import CorpusPanel from '$lib/features/workspace/components/CorpusPanel.svelte';
  import ProjectDashboard from '$lib/features/workspace/components/ProjectDashboard.svelte';
  import SelectionActionBar from '$lib/features/workspace/components/SelectionActionBar.svelte';
  import type { SelectionAction } from '$lib/features/workspace/components/SelectionActionBar.svelte';
  import MarkdownPanel from '$lib/features/workspace/panels/MarkdownPanel.svelte';
  import type { ReadingStatus } from '$lib/features/workspace/services/workspaceApi';
  import type { WorkspacePanelContext } from '$lib/features/workspace/types/panels';

  type Props = {
    context: WorkspacePanelContext;
  };

  type FocusSection = {
    label: string;
    description: string;
  };

  let { context }: Props = $props();

  const sectionsByType: Record<string, FocusSection[]> = {
    paper: [
      { label: 'Reading Note', description: 'Summary, methods, results.' },
      { label: 'Concepts', description: 'Ideas to reuse later.' },
      { label: 'Limits', description: 'Critique, gaps, questions.' }
    ],
    concept: [
      { label: 'Definition', description: 'Precise meaning.' },
      { label: 'Examples', description: 'Where it appears.' },
      { label: 'Evolution', description: 'How your understanding changes.' }
    ],
    project: [
      { label: 'Question', description: 'Research direction.' },
      { label: 'Hypotheses', description: 'Current assumptions.' },
      { label: 'Writing', description: 'Draftable output.' }
    ],
    brainstorm: [
      { label: 'Ideas', description: 'Fast capture.' },
      { label: 'Hypotheses', description: 'Things to test.' },
      { label: 'Decisions', description: 'What became stable.' }
    ],
    review: [
      { label: 'Corpus', description: 'Papers being synthesized.' },
      { label: 'Themes', description: 'Conceptual structure.' },
      { label: 'Gaps', description: 'Open space for contribution.' }
    ],
    note: [
      { label: 'Note', description: 'Free-form thinking.' },
      { label: 'Links', description: 'Related objects.' }
    ]
  };

  const titleByType: Record<string, string> = {
    paper: 'Reading Note',
    concept: 'Concept Workspace',
    project: 'Project Workspace',
    brainstorm: 'Brainstorm Workspace',
    review: 'Literature Review',
    note: 'Note'
  };

  const iconByType = {
    paper: BookOpen,
    concept: FileText,
    project: PenLine,
    brainstorm: Lightbulb,
    review: PenLine,
    note: StickyNote
  };

  let meta = $derived(entityMeta[context.object.type]);
  let title = $derived(titleByType[context.object.type]);
  let Icon = $derived(iconByType[context.object.type]);
  let sections = $derived(sectionsByType[context.object.type]);

  const readingStatuses: { value: ReadingStatus; label: string }[] = [
    { value: 'unread', label: 'Unread' },
    { value: 'reading', label: 'Reading' },
    { value: 'paused', label: 'Paused' },
    { value: 'reviewed', label: 'Reviewed' },
    { value: 'mastered', label: 'Mastered' }
  ];

  let currentReadingStatus = $derived(
    readingStatusFromContent(context.content)
  );

  function readingStatusFromContent(content: string): ReadingStatus {
    const match = content.match(/^status:\s*(.+)$/m);
    const status = match?.[1]?.trim().toLowerCase();
    if (
      status === 'unread' ||
      status === 'reading' ||
      status === 'paused' ||
      status === 'reviewed' ||
      status === 'mastered'
    ) {
      return status;
    }
    return 'unread';
  }

  async function setReadingStatus(status: ReadingStatus): Promise<void> {
    if (status === currentReadingStatus) return;
    await context.updateReadingStatus(status);
  }

  // Root scoping the contextual selection bar. Selecting a passage in the
  // reading notes (or the future PDF reader) reveals the relevant actions,
  // which stay hidden the rest of the time.
  let paperRoot = $state<HTMLElement | null>(null);
  let noteMode = $state<'reading' | 'editing'>('reading');

  let selectionActions = $derived<SelectionAction[]>([
    {
      id: 'concept',
      label: 'Create Concept',
      icon: entityMeta.concept.icon,
      iconClass: entityMeta.concept.text,
      run: context.createConceptFromSelection
    },
    {
      id: 'project',
      label: 'Add to Project',
      icon: entityMeta.project.icon,
      iconClass: entityMeta.project.text,
      run: context.createProjectFromSelection
    },
    {
      id: 'brainstorm',
      label: 'Start Brainstorm',
      icon: entityMeta.brainstorm.icon,
      iconClass: entityMeta.brainstorm.text,
      run: context.createBrainstormFromSelection
    },
    {
      id: 'review',
      label: 'Add to Review',
      icon: entityMeta.review.icon,
      iconClass: entityMeta.review.text,
      run: context.createReviewFromSelection
    }
  ]);
</script>

{#if context.object.type === 'paper'}
  <section class="flex min-h-0 flex-1 flex-col bg-background/95">
    <div class="border-b border-border px-6 py-4">
      <div class="flex min-w-0 items-start justify-between gap-4">
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <BookOpen size={17} class={meta.text} />
            <p class="text-xs font-medium uppercase text-accent">Paper</p>
          </div>
          <h3 class="mt-1 truncate text-lg font-semibold text-foreground">
            {context.object.title}
          </h3>
          <p class="mt-1 truncate text-sm text-muted-foreground">
            {context.object.subtitle || 'Reading source'}
          </p>
        </div>
        <span
          class="shrink-0 rounded-md border border-border bg-muted/20 px-2 py-1 text-xs text-muted-foreground"
        >
          {context.saveState === 'saving'
            ? 'Saving'
            : context.saveState === 'unsaved'
              ? 'Unsaved'
              : context.saveState === 'error'
                ? 'Save failed'
                : 'Saved'}
        </span>
      </div>

      <div class="mt-4 flex flex-wrap items-center gap-2">
        <button
          class="inline-flex h-9 items-center gap-2 rounded-md bg-accent px-3 text-sm font-medium text-accent-foreground transition hover:bg-accent/90"
          type="button"
          onclick={context.openPdf}
        >
          <ExternalLink size={15} />
          Open PDF
        </button>
        <div
          class="flex flex-wrap items-center gap-1 rounded-md border border-border bg-muted/15 p-1"
          aria-label="Reading status"
        >
          {#each readingStatuses as status}
            <button
              class={currentReadingStatus === status.value
                ? 'h-7 rounded bg-background px-2.5 text-xs font-medium text-foreground shadow-sm'
                : 'h-7 rounded px-2.5 text-xs text-muted-foreground transition hover:text-foreground'}
              type="button"
              onclick={() => setReadingStatus(status.value)}
            >
              {status.label}
            </button>
          {/each}
        </div>
      </div>
    </div>

    <div bind:this={paperRoot} class="min-h-0 flex-1 overflow-hidden">
      <section
        class="flex h-full min-h-0 flex-col overflow-hidden"
        aria-label="Reading notes"
      >
        <div
          class="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-border/70 px-6 py-3"
        >
          <p class="text-xs font-medium uppercase text-muted-foreground">
            Reading notes
          </p>
          <div
            class="flex items-center gap-1 rounded-md border border-border bg-muted/15 p-1"
            aria-label="Note mode"
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
        <div
          class:overflow-auto={noteMode === 'reading'}
          class:overflow-hidden={noteMode === 'editing'}
          class="min-h-0 flex-1"
        >
          {#if noteMode === 'reading'}
            <MarkdownPreview
              content={context.content}
              objectTitle={context.object.title}
              compact
              showMetadata={false}
            />
          {:else}
            <MarkdownPanel {context} />
          {/if}
        </div>
      </section>
    </div>

    <SelectionActionBar root={paperRoot} actions={selectionActions} />
  </section>
{:else if context.object.type === 'project'}
  <ProjectDashboard {context} />
{:else}
  <section class="flex min-h-0 flex-1 flex-col bg-background/95">
    <div class="border-b border-border px-6 py-4">
      <div class="flex min-w-0 items-start justify-between gap-4">
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <Icon size={17} class={meta.text} />
            <p class="text-xs font-medium uppercase text-accent">{title}</p>
          </div>
          <h3 class="mt-1 truncate text-lg font-semibold text-foreground">
            {context.object.title}
          </h3>
        </div>
        <span
          class="shrink-0 rounded-md border border-border bg-muted/25 px-2 py-1 text-xs text-muted-foreground"
        >
          {context.saveState === 'saving'
            ? 'Saving'
            : context.saveState === 'unsaved'
              ? 'Unsaved'
              : context.saveState === 'error'
                ? 'Save failed'
                : 'Saved'}
        </span>
      </div>

      <div class="mt-4 grid gap-2 md:grid-cols-3">
        {#each sections as section}
          <div
            class="rounded-md border border-border bg-muted/[0.08] px-3 py-2"
          >
            <p class="text-xs font-medium text-foreground">{section.label}</p>
            <p class="mt-1 line-clamp-1 text-xs text-muted-foreground">
              {section.description}
            </p>
          </div>
        {/each}
      </div>
    </div>

    {#if context.object.type === 'review'}
      <CorpusPanel {context} />
    {/if}

    <div
      class="flex shrink-0 items-center justify-end border-b border-border/70 px-6 py-2"
    >
      <div
        class="flex items-center gap-1 rounded-md border border-border bg-muted/15 p-1"
        aria-label="Note mode"
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

    <div
      class:overflow-auto={noteMode === 'reading'}
      class:overflow-hidden={noteMode === 'editing'}
      class="min-h-0 flex-1"
    >
      {#if noteMode === 'reading'}
        <MarkdownPreview
          content={context.content}
          objectTitle={context.object.title}
          compact
          showMetadata={false}
        />
      {:else}
        <MarkdownPanel {context} />
      {/if}
    </div>
  </section>
{/if}
