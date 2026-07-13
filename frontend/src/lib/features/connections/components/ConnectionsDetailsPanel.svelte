<script lang="ts">
  import { ExternalLink, Trash2 } from '@lucide/svelte';

  import { entityMeta } from '$lib/design/entities';
  import type { LinkableObject } from '$lib/features/linking/types/linking';
  import type {
    ConnectionType,
    ConnectionTypeDefinition,
    ObjectConnection
  } from '$lib/features/connections/types/connections';

  type Props = {
    object: LinkableObject | null;
    outgoing: ObjectConnection[];
    incoming: ObjectConnection[];
    relationDefinitions: ConnectionTypeDefinition[];
    onSelectObject: (object: LinkableObject) => void;
    onDeleteConnection: (connectionId: string) => void;
  };

  let {
    object,
    outgoing,
    incoming,
    relationDefinitions,
    onSelectObject,
    onDeleteConnection
  }: Props = $props();

  const relationById = $derived(
    Object.fromEntries(
      relationDefinitions.map((item) => [item.id, item])
    ) as Record<ConnectionType, ConnectionTypeDefinition>
  );
</script>

<aside
  class="telemetry-panel border-t border-border bg-background/88 p-4 xl:min-h-0 xl:overflow-y-auto xl:border-l xl:border-t-0"
>
  {#if object}
    {@const meta = entityMeta[object.type]}
    <div class="flex items-start gap-3">
      <div
        class="selected-node flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-border bg-muted/20"
      >
        <meta.icon size={18} class={meta.text} />
      </div>
      <div class="min-w-0">
        <p class="text-xs font-medium uppercase text-accent">
          Selected {meta.label}
        </p>
        <h2 class="mt-1 line-clamp-3 text-base font-semibold text-foreground">
          {object.title}
        </h2>
        {#if object.subtitle}
          <p class="mt-1 line-clamp-2 text-xs text-muted-foreground">
            {object.subtitle}
          </p>
        {/if}
      </div>
    </div>

    <div class="telemetry-stats mt-4 grid grid-cols-3 text-center">
      <div class="border-y border-border p-2">
        <p class="text-lg font-semibold text-foreground">
          {incoming.length + outgoing.length}
        </p>
        <p class="text-[11px] uppercase text-muted-foreground">Total</p>
      </div>
      <div class="border border-border p-2">
        <p class="text-lg font-semibold text-foreground">{outgoing.length}</p>
        <p class="text-[11px] uppercase text-muted-foreground">Out</p>
      </div>
      <div class="border-y border-border p-2">
        <p class="text-lg font-semibold text-foreground">{incoming.length}</p>
        <p class="text-[11px] uppercase text-muted-foreground">In</p>
      </div>
    </div>

    <a
      class="mt-4 inline-flex h-9 w-full items-center justify-center gap-2 rounded-md border border-border text-sm font-medium text-foreground hover:bg-muted"
      href={`/workspace?open=${encodeURIComponent(object.id)}`}
    >
      <ExternalLink size={15} />
      Open in Workspace
    </a>

    <section class="mt-5">
      <h3 class="text-[0.66rem] font-semibold uppercase text-muted-foreground">Outgoing signals</h3>
      <div class="mt-2 space-y-2">
        {#each outgoing as connection}
          <div class="relation-entry border-y border-border p-2">
            <div class="flex items-center justify-between gap-2">
              <p class="text-xs font-medium text-accent">
                {relationById[connection.relation_type]?.label}
              </p>
              <button
                class="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                type="button"
                aria-label="Delete connection"
                onclick={() => onDeleteConnection(connection.id)}
              >
                <Trash2 size={13} />
              </button>
            </div>
            <button
              class="mt-1 block w-full truncate text-left text-sm text-foreground hover:text-accent"
              type="button"
              onclick={() => onSelectObject(connection.target)}
            >
              {connection.target.title}
            </button>
          </div>
        {:else}
          <p class="text-sm text-muted-foreground">No outgoing relations.</p>
        {/each}
      </div>
    </section>

    <section class="mt-5">
      <h3 class="text-[0.66rem] font-semibold uppercase text-muted-foreground">Incoming signals</h3>
      <div class="mt-2 space-y-2">
        {#each incoming as connection}
          <div class="relation-entry border-y border-border p-2">
            <div class="flex items-center justify-between gap-2">
              <p class="text-xs font-medium text-muted-foreground">
                {relationById[connection.relation_type]?.inverse_label}
              </p>
              <button
                class="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                type="button"
                aria-label="Delete connection"
                onclick={() => onDeleteConnection(connection.id)}
              >
                <Trash2 size={13} />
              </button>
            </div>
            <button
              class="mt-1 block w-full truncate text-left text-sm text-foreground hover:text-accent"
              type="button"
              onclick={() => onSelectObject(connection.source)}
            >
              {connection.source.title}
            </button>
          </div>
        {:else}
          <p class="text-sm text-muted-foreground">No incoming relations.</p>
        {/each}
      </div>
    </section>
  {:else}
    <p class="text-sm text-muted-foreground">Select an object.</p>
  {/if}
</aside>

<style>
  .telemetry-panel {
    position: relative;
  }

  .telemetry-panel::before {
    content: '';
    position: absolute;
    left: -1px;
    top: 70px;
    width: 1px;
    height: 92px;
    background: hsl(var(--accent) / 0.5);
    box-shadow: 0 0 9px hsl(var(--accent) / 0.22);
  }

  .selected-node {
    position: relative;
  }

  .selected-node::after {
    content: '';
    position: absolute;
    right: 5px;
    top: 5px;
    width: 4px;
    height: 4px;
    background: hsl(var(--accent));
    box-shadow: 0 0 6px hsl(var(--accent) / 0.6);
  }

  .telemetry-stats > div + div {
    margin-left: -1px;
  }

  .relation-entry {
    background: hsl(var(--background) / 0.52);
  }
</style>
