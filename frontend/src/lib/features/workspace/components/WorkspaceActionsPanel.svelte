<script lang="ts">
  import { Link2, Plus } from '@lucide/svelte';
  import { onDestroy } from 'svelte';

  import TagBadges from '$lib/components/ui/TagBadges.svelte';
  import TagEditor from '$lib/components/ui/TagEditor.svelte';
  import { entityMeta } from '$lib/design/entities';
  import type {
    LinkableObject,
    LinkableType
  } from '$lib/features/linking/types/linking';
  import MetadataSummary from '$lib/features/workspace/components/MetadataSummary.svelte';
  import RelationRow from '$lib/features/workspace/components/RelationRow.svelte';
  import { setObjectTags } from '$lib/features/workspace/services/workspaceApi';
  import RelationsPanel from '$lib/features/workspace/panels/RelationsPanel.svelte';
  import type { WorkspacePanelContext } from '$lib/features/workspace/types/panels';

  type Props = {
    context: WorkspacePanelContext;
    labels: Record<LinkableType, string>;
  };

  type TargetKind = LinkableType;

  let { context, labels }: Props = $props();

  let headerMeta = $derived(entityMeta[context.object.type]);
  let HeaderIcon = $derived(headerMeta.icon);

  let conceptTitle = $state('');
  let projectTitle = $state('');
  let reviewTitle = $state('');
  let brainstormTitle = $state('');
  let targetQuery = $state('');
  let targetKind = $state<TargetKind>('paper');
  let targetResults = $state<LinkableObject[]>([]);
  let busy = $state('');
  let message = $state<string | null>(null);
  let searchTimer: ReturnType<typeof setTimeout> | null = null;
  let searchRequest = 0;
  let actionCopy = $derived({
    concept:
      context.object.type === 'concept'
        ? 'Create Related Concept'
        : 'Create Concept',
    project:
      context.object.type === 'project'
        ? 'Add Related Project'
        : 'Add to Project',
    brainstorm:
      context.object.type === 'brainstorm'
        ? 'Create Follow-up Idea'
        : 'Create Research Idea',
    review:
      context.object.type === 'review'
        ? 'Create Related Review'
        : 'Add to Literature Review',
    projectPlaceholder:
      context.object.type === 'project' ? 'Related project' : 'New project',
    reviewPlaceholder:
      context.object.type === 'review' ? 'Related review' : 'New review'
  });

  $effect(() => {
    void targetQuery;
    void targetKind;
    scheduleTargetSearch();
  });

  function scheduleTargetSearch(): void {
    if (searchTimer) clearTimeout(searchTimer);
    const query = targetQuery;
    const kind = targetKind;
    const request = ++searchRequest;
    searchTimer = setTimeout(async () => {
      const results = await context.searchObjects(query);
      if (request !== searchRequest) return;
      targetResults = results.filter(
        (item) => item.type === kind && item.id !== context.object.id
      );
    }, 170);
  }

  onDestroy(() => {
    if (searchTimer) clearTimeout(searchTimer);
    searchRequest += 1;
  });

  async function runAction(
    name: string,
    action: () => Promise<void>
  ): Promise<void> {
    busy = name;
    message = null;
    try {
      await action();
      message = 'Workspace updated.';
    } catch (error) {
      message = error instanceof Error ? error.message : 'Action failed.';
    } finally {
      busy = '';
    }
  }

  async function createConcept(): Promise<void> {
    const title = conceptTitle.trim();
    if (!title) return;
    await runAction('concept', async () => {
      await context.createConceptFromTitle(title);
      conceptTitle = '';
    });
  }

  async function createProject(): Promise<void> {
    const title = projectTitle.trim();
    if (!title) return;
    await runAction('project', async () => {
      await context.createProjectFromTitle(title);
      projectTitle = '';
    });
  }

  async function createReview(): Promise<void> {
    const title = reviewTitle.trim();
    if (!title) return;
    await runAction('review', async () => {
      await context.createReviewFromTitle(title);
      reviewTitle = '';
    });
  }

  async function createBrainstorm(): Promise<void> {
    const title = brainstormTitle.trim();
    if (!title) return;
    await runAction('brainstorm', async () => {
      await context.createBrainstormFromTitle(title);
      brainstormTitle = '';
    });
  }

  async function linkTarget(target: LinkableObject): Promise<void> {
    await runAction(`link-${target.id}`, async () => {
      await context.linkObjectToTarget(target);
    });
  }

  async function saveTags(next: string[]): Promise<void> {
    await setObjectTags(context.object.id, next);
    await context.refreshObject();
  }
</script>

<aside
  class="right-panel flex min-w-0 flex-col gap-5 overflow-x-hidden overflow-y-auto border-l border-border bg-background/70 px-5 py-5"
>
  <!-- OBJECT -->
  <header class="flex items-start gap-2.5">
    <span
      class={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md border ${headerMeta.border} ${headerMeta.tint}`}
    >
      <HeaderIcon size={16} class={headerMeta.text} />
    </span>
    <div class="min-w-0 flex-1">
      <p class="text-[0.7rem] font-semibold uppercase tracking-[0.08em] text-accent">
        {labels[context.object.type]}
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
    <p class="ros-section-label">Actions</p>
    <div class="mt-3 grid gap-2.5">
      {#each [{ kind: 'concept', meta: entityMeta.concept, copy: actionCopy.concept, value: conceptTitle, placeholder: 'Concept title', run: createConcept }, { kind: 'project', meta: entityMeta.project, copy: actionCopy.project, value: projectTitle, placeholder: actionCopy.projectPlaceholder, run: createProject }, { kind: 'brainstorm', meta: entityMeta.brainstorm, copy: actionCopy.brainstorm, value: brainstormTitle, placeholder: 'Research idea', run: createBrainstorm }, { kind: 'review', meta: entityMeta.review, copy: actionCopy.review, value: reviewTitle, placeholder: actionCopy.reviewPlaceholder, run: createReview }] as action (action.kind)}
        {@const ActionIcon = action.meta.icon}
        <div class={`rounded-lg border p-2.5 ${action.meta.border} ${action.meta.tint}`}>
          <div class="mb-2 flex items-center gap-1.5">
            <ActionIcon size={14} class={action.meta.text} />
            <h3 class={`text-xs font-semibold ${action.meta.text}`}>
              {action.copy}
            </h3>
          </div>
          <div class="flex gap-2">
            {#if action.kind === 'concept'}
              <input
                bind:value={conceptTitle}
                class="ros-input"
                placeholder={action.placeholder}
                onkeydown={(event) => event.key === 'Enter' && createConcept()}
              />
            {:else if action.kind === 'project'}
              <input
                bind:value={projectTitle}
                class="ros-input"
                placeholder={action.placeholder}
                onkeydown={(event) => event.key === 'Enter' && createProject()}
              />
            {:else if action.kind === 'brainstorm'}
              <input
                bind:value={brainstormTitle}
                class="ros-input"
                placeholder={action.placeholder}
                onkeydown={(event) => event.key === 'Enter' && createBrainstorm()}
              />
            {:else}
              <input
                bind:value={reviewTitle}
                class="ros-input"
                placeholder={action.placeholder}
                onkeydown={(event) => event.key === 'Enter' && createReview()}
              />
            {/if}
            <button
              class="ros-btn-icon"
              type="button"
              aria-label={action.copy}
              disabled={!action.value.trim() || busy === action.kind}
              onclick={action.run}
            >
              <Plus size={15} />
            </button>
          </div>
        </div>
      {/each}
    </div>
  </section>

  <!-- QUICK LINKS -->
  <section class="border-t border-border pt-4">
    <p class="ros-section-label"><Link2 size={13} /> Quick Links</p>
    <div
      class="mt-3 grid grid-cols-5 gap-1 rounded-md border border-border bg-background p-1"
    >
      {#each ['paper', 'concept', 'project', 'brainstorm', 'review'] as type}
        {@const TypeIcon = entityMeta[type as LinkableType].icon}
        <button
          class={targetKind === type
            ? 'flex h-7 items-center justify-center rounded bg-muted text-foreground'
            : 'flex h-7 items-center justify-center rounded text-muted-foreground hover:text-foreground'}
          type="button"
          aria-label={labels[type as LinkableType]}
          title={labels[type as LinkableType]}
          onclick={() => (targetKind = type as TargetKind)}
        >
          <TypeIcon
            size={14}
            class={targetKind === type ? entityMeta[type as LinkableType].text : ''}
          />
        </button>
      {/each}
    </div>
    <input
      bind:value={targetQuery}
      class="ros-input mt-2"
      placeholder="Search existing object..."
    />
    <div class="mt-2 grid max-h-56 gap-1.5 overflow-auto">
      {#each targetResults.slice(0, 8) as item}
        <RelationRow object={item} onclick={() => linkTarget(item)}>
          {#snippet trailing()}
            <Plus size={13} />
          {/snippet}
        </RelationRow>
      {:else}
        <p class="px-1 py-1.5 text-xs text-muted-foreground">
          No matching object.
        </p>
      {/each}
    </div>
  </section>

  <!-- RELATIONS -->
  <section class="border-t border-border pt-4">
    <p class="ros-section-label">Relations</p>
    <div class="mt-3">
      <RelationsPanel {context} {labels} compact />
    </div>
  </section>

  <!-- METADATA -->
  <section class="border-t border-border pt-4">
    <p class="ros-section-label">Metadata</p>
    <div class="mt-3 grid gap-1">
      <span class="text-xs text-muted-foreground">Tags</span>
      <TagEditor tags={context.detail?.tags} onSave={saveTags} />
    </div>
    <div class="mt-3">
      <MetadataSummary {context} />
    </div>
  </section>
</aside>
