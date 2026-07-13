<script lang="ts">
  import { entityMeta, entityTypes } from '$lib/design/entities';
  import type { LinkableType } from '$lib/features/linking/types/linking';
  import type {
    ConnectionType,
    ConnectionTypeDefinition
  } from '$lib/features/connections/types/connections';

  let {
    objectTypes,
    relationTypes,
    relationDefinitions,
    onToggleObjectType,
    onToggleRelationType
  } = $props<{
    objectTypes: Set<LinkableType>;
    relationTypes: Set<ConnectionType>;
    relationDefinitions: ConnectionTypeDefinition[];
    onToggleObjectType: (type: LinkableType) => void;
    onToggleRelationType: (type: ConnectionType) => void;
  }>();
</script>

<div
  class="filter-bus grid gap-3 border-b border-border bg-muted/[0.045] px-4 py-3 xl:grid-cols-2"
>
  <section>
    <p class="text-[0.63rem] font-semibold uppercase text-muted-foreground">
      Object types
    </p>
    <div class="mt-2 flex flex-wrap gap-1.5">
      {#each entityTypes as type}
        {@const meta = entityMeta[type]}
        <button
          class={objectTypes.has(type)
            ? 'inline-flex h-7 items-center gap-1.5 rounded-md border border-accent/30 bg-background px-2 text-[0.66rem] font-medium text-foreground'
            : 'inline-flex h-7 items-center gap-1.5 rounded-md border border-border bg-transparent px-2 text-[0.66rem] font-medium text-muted-foreground opacity-55'}
          type="button"
          aria-pressed={objectTypes.has(type)}
          onclick={() => onToggleObjectType(type)}
        >
          <meta.icon size={14} class={meta.text} />
          {meta.plural}
        </button>
      {/each}
    </div>
  </section>

  <section>
    <p class="text-[0.63rem] font-semibold uppercase text-muted-foreground">
      Relation types
    </p>
    <div class="mt-2 flex flex-wrap gap-1.5">
      {#each relationDefinitions as relation}
        <button
          class={relationTypes.has(relation.id)
            ? 'h-7 rounded-md border border-accent/30 bg-background px-2 text-[0.66rem] font-medium text-foreground'
            : 'h-7 rounded-md border border-border bg-transparent px-2 text-[0.66rem] font-medium text-muted-foreground opacity-55'}
          type="button"
          title={relation.description}
          aria-pressed={relationTypes.has(relation.id)}
          onclick={() => onToggleRelationType(relation.id)}
        >
          {relation.label}
        </button>
      {/each}
    </div>
  </section>
</div>

<style>
  .filter-bus {
    position: relative;
  }

  .filter-bus::before {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    top: 0;
    width: 2px;
    background: hsl(var(--accent) / 0.46);
  }
</style>
