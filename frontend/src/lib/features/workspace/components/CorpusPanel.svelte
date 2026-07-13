<script lang="ts">
  import { entityMeta } from '$lib/design/entities';
  import type {
    LinkableObject,
    LinkableType
  } from '$lib/features/linking/types/linking';
  import type { CorpusEntry } from '$lib/features/research-explorer/types/researchExplorer';
  import type { WorkspacePanelContext } from '$lib/features/workspace/types/panels';

  type Props = {
    context: WorkspacePanelContext;
  };

  type CorpusGroup = {
    type: LinkableType;
    label: string;
    items: CorpusEntry[];
  };

  let { context }: Props = $props();

  const groupTypes: LinkableType[] = [
    'paper',
    'concept',
    'brainstorm',
    'review',
    'project'
  ];

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
      .map((item) => ({ object: item, roles: [] }));
  }

  function corpusEntries(type: LinkableType): CorpusEntry[] {
    const entries = context.detail?.corpus?.[type];
    if (entries?.length) {
      return [...entries].sort((a, b) =>
        a.object.title.localeCompare(b.object.title)
      );
    }
    return fallbackEntries(type);
  }

  let groups = $derived<CorpusGroup[]>(
    groupTypes
      .map((type) => ({
        type,
        label: entityMeta[type].plural,
        items: corpusEntries(type)
      }))
      .filter((group) => group.items.length > 0)
  );
</script>

<section class="border-b border-border bg-muted/[0.06] px-6 py-4">
  <div class="flex items-center justify-between gap-3">
    <div>
      <p class="text-xs font-medium uppercase text-accent">Corpus</p>
      <h3 class="mt-1 text-sm font-semibold text-foreground">
        Linked research objects
      </h3>
    </div>
    <span class="text-xs text-muted-foreground">
      {groups.reduce((total, group) => total + group.items.length, 0)} objects
    </span>
  </div>

  <div class="mt-4 grid gap-3 xl:grid-cols-2">
    {#each groups as group}
      {@const meta = entityMeta[group.type]}
      <section class="rounded-lg border border-border bg-background/55">
        <div
          class="flex items-center justify-between gap-2 border-b border-border px-3 py-2"
        >
          <div class="flex items-center gap-2">
            <meta.icon size={14} class={meta.text} />
            <h4 class="text-xs font-medium uppercase text-muted-foreground">
              {group.label}
            </h4>
          </div>
          <span class="text-xs text-muted-foreground">
            {group.items.length}
          </span>
        </div>
        <div class="max-h-44 overflow-auto p-1">
          {#each group.items as entry}
            {@const item = entry.object}
            <button
              class="flex w-full items-start justify-between gap-3 rounded-md px-2 py-2 text-left text-sm text-muted-foreground hover:bg-muted/45 hover:text-foreground"
              type="button"
              onclick={() => context.openObject(item)}
            >
              <span class="min-w-0">
                <span class="block truncate">{item.title}</span>
                {#if entry.roles.length}
                  <span class="mt-1 flex flex-wrap gap-1">
                    {#each entry.roles as role}
                      <span
                        class="rounded border border-border bg-muted/35 px-1.5 py-0.5 text-[10px] font-medium uppercase text-muted-foreground"
                      >
                        {role}
                      </span>
                    {/each}
                  </span>
                {/if}
              </span>
              {#if item.subtitle && !entry.roles.length}
                <span
                  class="hidden max-w-24 shrink-0 truncate text-xs md:block"
                >
                  {item.subtitle}
                </span>
              {/if}
            </button>
          {/each}
        </div>
      </section>
    {:else}
      <p
        class="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground"
      >
        No corpus links yet. Add papers, concepts, brainstorms or reviews from
        the action panel.
      </p>
    {/each}
  </div>
</section>
