<script lang="ts">
  import { ArrowDownLeft, ArrowUpRight, Link2 } from '@lucide/svelte';

  import { entityMeta } from '$lib/design/entities';
  import type { LinkableObject } from '$lib/features/linking/types/linking';
  import type {
    ConnectionType,
    ConnectionTypeDefinition
  } from '$lib/features/connections/types/connections';
  import type { StructureGroup } from '$lib/features/connections/types/knowledgeGraph';

  type Props = {
    current: LinkableObject;
    groups: StructureGroup[];
    relationDefinitions: ConnectionTypeDefinition[];
    onSelectObject: (object: LinkableObject) => void;
  };

  let { current, groups, relationDefinitions, onSelectObject }: Props =
    $props();

  const relationById = $derived(
    Object.fromEntries(
      relationDefinitions.map((item) => [item.id, item])
    ) as Record<ConnectionType, ConnectionTypeDefinition>
  );
  const currentMeta = $derived(entityMeta[current.type]);
</script>

<section class="connection-list min-w-0 flex-1 overflow-y-auto p-5">
  <div class="list-heading border-b border-border pb-4">
    <p class="text-[0.66rem] font-semibold uppercase text-accent">
      Connection list · {currentMeta.label}
    </p>
    <h2 class="mt-2 line-clamp-2 text-2xl font-semibold text-foreground">
      {current.title}
    </h2>
    {#if current.subtitle}
      <p class="mt-2 line-clamp-2 text-sm text-muted-foreground">
        {current.subtitle}
      </p>
    {/if}
  </div>

  <div class="mt-4 space-y-3">
    {#each groups as group}
      {@const meta = entityMeta[group.type]}
      <section class="relation-group border-block border-y border-border bg-background/58">
        <div
          class="flex items-center justify-between gap-3 border-b border-border px-4 py-3"
        >
          <div class="flex items-center gap-2">
            <meta.icon size={16} class={meta.text} />
            <h3 class="text-sm font-semibold text-foreground">
              {meta.plural}
            </h3>
          </div>
          <span class="text-xs text-muted-foreground">
            {group.items.length}
          </span>
        </div>

        <div class="divide-y divide-border">
          {#each group.items as item}
            {@const relation = relationById[item.connection.relation_type]}
            <button
              class="grid w-full gap-2 px-4 py-3 text-left hover:bg-muted/20 md:grid-cols-[160px_minmax(0,1fr)] md:items-center"
              type="button"
              onclick={() => onSelectObject(item.object)}
            >
              <span
                class={item.direction === 'outgoing'
                  ? 'inline-flex items-center gap-1.5 text-xs font-medium text-accent'
                  : 'inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground'}
              >
                {#if item.direction === 'outgoing'}
                  <ArrowUpRight size={13} />
                  {relation?.label}
                {:else}
                  <ArrowDownLeft size={13} />
                  {relation?.inverse_label}
                {/if}
              </span>
              <span class="min-w-0">
                <span
                  class="block truncate text-sm font-medium text-foreground"
                >
                  {item.object.title}
                </span>
                {#if item.object.subtitle}
                  <span
                    class="mt-0.5 block truncate text-xs text-muted-foreground"
                  >
                    {item.object.subtitle}
                  </span>
                {/if}
              </span>
            </button>
          {/each}
        </div>
      </section>
    {:else}
      <div class="border-block border-y border-border bg-muted/[0.04] p-10 text-center">
        <Link2 class="mx-auto text-muted-foreground" size={28} />
        <p class="mt-3 text-sm text-muted-foreground">
          No visible connections for this object.
        </p>
      </div>
    {/each}
  </div>
</section>

<style>
  .connection-list {
    background: hsl(var(--background) / 0.76);
  }

  .list-heading {
    position: relative;
  }

  .list-heading::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    width: 110px;
    height: 1px;
    background: hsl(var(--accent) / 0.64);
  }

  .relation-group {
    position: relative;
  }

  .relation-group::before {
    content: '';
    position: absolute;
    left: -9px;
    top: 16px;
    width: 7px;
    height: 7px;
    border: 1px solid hsl(var(--accent) / 0.5);
    background: hsl(var(--background));
  }
</style>
