<script lang="ts">
  import { entityMeta } from '$lib/design/entities';
  import type { LinkableType } from '$lib/features/linking/types/linking';
  import type { WorkspacePanelContext } from '$lib/features/workspace/types/panels';

  type Props = {
    context: WorkspacePanelContext;
    labels: Record<LinkableType, string>;
    mode?: 'outgoing' | 'incoming';
    compact?: boolean;
  };

  const types: LinkableType[] = [
    'paper',
    'concept',
    'project',
    'brainstorm',
    'review',
    'note'
  ];

  let { context, labels, mode = 'outgoing', compact = false }: Props = $props();
  let groups = $derived(
    mode === 'incoming' ? context.detail?.backlinks : context.detail?.related
  );
  let empty = $derived(types.every((type) => !groups?.[type]?.length));
</script>

<section
  class={compact
    ? 'grid gap-3'
    : 'min-h-0 flex-1 overflow-auto bg-background/95 p-6'}
>
  <div class={compact ? 'w-full' : 'mx-auto w-full max-w-4xl'}>
    {#if !compact}
      <p class="text-xs font-medium uppercase text-accent">
        {mode === 'incoming' ? 'Backlinks' : 'Relations'}
      </p>
      <h3 class="mt-2 text-xl font-semibold text-foreground">
        {context.object.title}
      </h3>
    {/if}

    <div class={compact ? 'grid gap-3' : 'mt-6 grid gap-5'}>
      {#each types as type}
        {@const items = groups?.[type] ?? []}
        {@const meta = entityMeta[type]}
        {@const Icon = meta.icon}
        {#if items.length}
          <section
            class={`rounded-lg border ${meta.border} ${meta.tint} ${compact ? 'p-3' : 'p-4'}`}
          >
            <h4
              class={`flex items-center gap-1.5 text-xs font-medium uppercase ${meta.text}`}
            >
              <Icon size={13} />
              {mode === 'incoming' ? 'Linked from' : 'Related'}
              {labels[type]}
            </h4>
            <div class="mt-2.5 grid gap-1.5">
              {#each items as item}
                <button
                  class={`ros-row ${meta.borderLeft}`}
                  type="button"
                  onclick={() => context.openObject(item)}
                >
                  <span class="min-w-0 flex-1">
                    <span
                      class="block truncate text-sm leading-tight text-foreground"
                      >{item.title}</span
                    >
                    {#if item.subtitle}
                      <span
                        class="mt-0.5 block truncate text-xs leading-tight text-muted-foreground"
                        >{item.subtitle}</span
                      >
                    {/if}
                  </span>
                </button>
              {/each}
            </div>
          </section>
        {/if}
      {/each}
    </div>

    {#if empty && !compact}
      <p class="mt-5 text-sm text-muted-foreground">
        No relations yet. Links will appear here once this object is connected
        to the Vault.
      </p>
    {/if}
  </div>
</section>
