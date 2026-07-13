<script lang="ts">
  import {
    ListTree,
    Network,
    Plus,
    Search,
    SlidersHorizontal,
    X
  } from '@lucide/svelte';
  import { onMount } from 'svelte';

  import { entityMeta } from '$lib/design/entities';
  import ConnectionsDetailsPanel from '$lib/features/connections/components/ConnectionsDetailsPanel.svelte';
  import ConnectionsFilters from '$lib/features/connections/components/ConnectionsFilters.svelte';
  import GraphView from '$lib/features/connections/components/GraphView.svelte';
  import StructureView from '$lib/features/connections/components/StructureView.svelte';
  import {
    createDefaultFilters,
    buildLocalGraph,
    buildStructureGroups
  } from '$lib/features/connections/services/knowledgeGraphBuilder';
  import {
    createConnection,
    deleteConnection,
    getConnectionGraph,
    getConnectionTypes,
    getObjectConnections,
    searchConnectionObjects
  } from '$lib/features/connections/services/connectionsApi';
  import type {
    LinkableObject,
    LinkableType
  } from '$lib/features/linking/types/linking';
  import type {
    ConnectionGraphData,
    ConnectionList,
    ConnectionType,
    ConnectionTypeDefinition
  } from '$lib/features/connections/types/connections';
  import {
    connectionTypes,
    defaultConnectionTypeDefinitions
  } from '$lib/features/connections/types/connections';
  import type { KnowledgeGraphFilters } from '$lib/features/connections/types/knowledgeGraph';

  type ViewMode = 'list' | 'graph';

  let viewMode = $state<ViewMode>('graph');
  let filtersOpen = $state(false);
  let query = $state('');
  let targetQuery = $state('');
  let objects = $state<LinkableObject[]>([]);
  let targetResults = $state<LinkableObject[]>([]);
  let selected = $state<LinkableObject | null>(null);
  let connections = $state<ConnectionList | null>(null);
  let graphData = $state<ConnectionGraphData>({ nodes: [], edges: [] });
  let relationDefinitions = $state<ConnectionTypeDefinition[]>(
    defaultConnectionTypeDefinitions
  );
  let filters = $state<KnowledgeGraphFilters>(
    createDefaultFilters(connectionTypes)
  );
  let creating = $state(false);
  let selectedType = $state<ConnectionType>('related');
  let selectedTarget = $state<LinkableObject | null>(null);
  let loading = $state(true);
  let message = $state<string | null>(null);
  let graphDepth = $state(1);
  let searchTimer: ReturnType<typeof setTimeout> | null = null;
  let targetTimer: ReturnType<typeof setTimeout> | null = null;

  const structureGroups = $derived(
    selected && connections
      ? buildStructureGroups(
          selected,
          connections.outgoing,
          connections.incoming,
          filters
        )
      : []
  );

  const localGraph = $derived(
    selected
      ? buildLocalGraph(graphData, selected, filters, graphDepth)
      : { nodes: [], edges: [] }
  );

  const filteredOutgoing = $derived(
    connections
      ? connections.outgoing.filter(
          (connection) =>
            filters.objectTypes.has(connection.target.type) &&
            filters.relationTypes.has(connection.relation_type)
        )
      : []
  );

  const filteredIncoming = $derived(
    connections
      ? connections.incoming.filter(
          (connection) =>
            filters.objectTypes.has(connection.source.type) &&
            filters.relationTypes.has(connection.relation_type)
        )
      : []
  );

  $effect(() => {
    void query;
    if (!loading) scheduleSearch();
  });

  $effect(() => {
    void targetQuery;
    if (creating) scheduleTargetSearch();
  });

  onMount(async () => {
    const [initialObjects, typeResponse, graph] = await Promise.all([
      searchConnectionObjects(''),
      getConnectionTypes().catch(() => ({
        relation_types: defaultConnectionTypeDefinitions
      })),
      getConnectionGraph()
    ]);
    objects = initialObjects;
    relationDefinitions = typeResponse.relation_types;
    filters = createDefaultFilters(
      typeResponse.relation_types.map((item) => item.id)
    );
    graphData = graph;
    if (objects[0]) await selectObject(objects[0]);
    loading = false;
  });

  function scheduleSearch(): void {
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(async () => {
      objects = await searchConnectionObjects(query);
    }, 140);
  }

  function scheduleTargetSearch(): void {
    if (targetTimer) clearTimeout(targetTimer);
    targetTimer = setTimeout(async () => {
      targetResults = (await searchConnectionObjects(targetQuery)).filter(
        (item) => item.id !== selected?.id
      );
    }, 140);
  }

  async function selectObject(item: LinkableObject): Promise<void> {
    selected = item;
    creating = false;
    selectedTarget = null;
    targetQuery = '';
    message = null;
    connections = await getObjectConnections(item.id);
  }

  function beginCreate(): void {
    creating = true;
    selectedTarget = null;
    targetQuery = '';
    targetResults = objects
      .filter((item) => item.id !== selected?.id)
      .slice(0, 8);
  }

  async function confirmCreate(): Promise<void> {
    if (!selected || !selectedTarget) return;
    await createConnection(selected.id, selectedTarget.id, selectedType);
    await refreshSelected();
    creating = false;
    selectedTarget = null;
    targetQuery = '';
    message = 'Connection created.';
  }

  async function removeConnection(connectionId: string): Promise<void> {
    await deleteConnection(connectionId);
    await refreshSelected();
    message = 'Connection removed.';
  }

  async function refreshSelected(): Promise<void> {
    if (!selected) return;
    const [nextConnections, nextGraph] = await Promise.all([
      getObjectConnections(selected.id),
      getConnectionGraph()
    ]);
    connections = nextConnections;
    graphData = nextGraph;
  }

  function toggleObjectType(type: LinkableType): void {
    const next = new Set(filters.objectTypes);
    if (next.has(type)) next.delete(type);
    else next.add(type);
    filters = { ...filters, objectTypes: next };
  }

  function toggleRelationType(type: ConnectionType): void {
    const next = new Set(filters.relationTypes);
    if (next.has(type)) next.delete(type);
    else next.add(type);
    filters = { ...filters, relationTypes: next };
  }
</script>

<section
  class="map-system grid min-h-[calc(100vh-4rem)] grid-cols-1 xl:h-[calc(100vh-4rem)] xl:grid-cols-[276px_minmax(0,1fr)_304px] xl:overflow-hidden"
>
  <aside
    class="map-index border-b border-border bg-background/88 p-4 xl:min-h-0 xl:overflow-hidden xl:border-b-0 xl:border-r"
  >
    <div class="flex items-center gap-3">
      <span class="map-core" aria-hidden="true">
        <Network size={17} />
      </span>
      <div class="min-w-0">
        <p class="text-[0.66rem] font-semibold uppercase text-accent">
          Network module
        </p>
        <h1 class="mt-0.5 text-xl font-semibold text-foreground">
          Knowledge Map
        </h1>
      </div>
      <span class="map-count">{objects.length}</span>
    </div>

    <label
      class="mt-5 flex h-10 items-center gap-2 rounded-md border border-border bg-muted/25 px-3 text-sm text-muted-foreground focus-within:border-accent/45"
    >
      <Search size={15} />
      <input
        bind:value={query}
        class="min-w-0 flex-1 bg-transparent text-foreground outline-none"
        placeholder="Find object"
        type="search"
      />
    </label>

    <div class="map-object-list mt-4 space-y-0.5 overflow-auto">
      {#if loading}
        <p class="text-sm text-muted-foreground">Loading objects...</p>
      {:else}
        {#each objects.slice(0, 50) as object}
          {@const meta = entityMeta[object.type]}
          <button
            class={selected?.id === object.id
              ? 'map-object map-object--active flex w-full items-center gap-3 px-3 py-2.5 text-left'
              : 'map-object flex w-full items-center gap-3 px-3 py-2.5 text-left text-muted-foreground hover:bg-muted/20 hover:text-foreground'}
            type="button"
            onclick={() => selectObject(object)}
          >
            <meta.icon size={15} class={meta.text} />
            <span class="min-w-0">
              <span class="block truncate text-sm font-medium">
                {object.title}
              </span>
              <span class="mt-0.5 block truncate text-xs">
                {meta.label}
              </span>
            </span>
          </button>
        {:else}
          <p class="text-sm text-muted-foreground">No objects found.</p>
        {/each}
      {/if}
    </div>
  </aside>

  <main class="map-canvas flex min-w-0 flex-col overflow-hidden">
    <header
      class="map-toolbar flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3"
    >
      <div
        class="inline-flex rounded-md border border-border bg-muted/[0.08] p-1"
      >
        <button
          class={viewMode === 'graph'
            ? 'inline-flex h-8 items-center gap-2 rounded-md bg-background px-3 text-xs font-medium text-foreground shadow-sm'
            : 'inline-flex h-8 items-center gap-2 rounded-md px-3 text-xs font-medium text-muted-foreground hover:text-foreground'}
          type="button"
          onclick={() => (viewMode = 'graph')}
        >
          <Network size={14} />
          Graph
        </button>
        <button
          class={viewMode === 'list'
            ? 'inline-flex h-8 items-center gap-2 rounded-md bg-background px-3 text-xs font-medium text-foreground shadow-sm'
            : 'inline-flex h-8 items-center gap-2 rounded-md px-3 text-xs font-medium text-muted-foreground hover:text-foreground'}
          type="button"
          onclick={() => (viewMode = 'list')}
        >
          <ListTree size={14} />
          List
        </button>
      </div>

      <div class="flex items-center gap-2">
        <button
          class={filtersOpen
            ? 'inline-flex h-9 items-center gap-2 rounded-md border border-accent/45 bg-accent/10 px-3 text-xs font-medium text-foreground'
            : 'inline-flex h-9 items-center gap-2 rounded-md border border-border bg-muted/[0.08] px-3 text-xs font-medium text-muted-foreground hover:text-foreground'}
          type="button"
          aria-expanded={filtersOpen}
          onclick={() => (filtersOpen = !filtersOpen)}
        >
          <SlidersHorizontal size={14} />
          Filters
        </button>
        <button
          class="inline-flex h-9 items-center gap-2 rounded-md bg-accent px-3 text-sm font-medium text-accent-foreground hover:bg-accent/90"
          type="button"
          onclick={beginCreate}
          disabled={!selected}
        >
          <Plus size={15} />
          Create Connection
        </button>
      </div>
    </header>

    {#if filtersOpen}
      <ConnectionsFilters
        objectTypes={filters.objectTypes}
        relationTypes={filters.relationTypes}
        {relationDefinitions}
        onToggleObjectType={toggleObjectType}
        onToggleRelationType={toggleRelationType}
      />
    {/if}

    {#if creating}
      <section class="border-b border-border bg-background p-4">
        <div class="flex items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-foreground">New Connection</h3>
          <button
            class="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
            type="button"
            aria-label="Cancel connection"
            onclick={() => (creating = false)}
          >
            <X size={15} />
          </button>
        </div>
        <div class="mt-4 grid gap-3 lg:grid-cols-[180px_minmax(0,1fr)_auto]">
          <select
            bind:value={selectedType}
            class="h-10 rounded-md border border-border bg-background px-3 text-sm text-foreground outline-none"
          >
            {#each relationDefinitions as type}
              <option value={type.id}>{type.label}</option>
            {/each}
          </select>
          <div class="relative">
            <input
              bind:value={targetQuery}
              class="h-10 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground outline-none focus:border-accent/45"
              placeholder="Search object to connect"
              type="search"
            />
            <div
              class="mt-2 max-h-56 overflow-auto rounded-md border border-border bg-background"
            >
              {#each targetResults.slice(0, 8) as object}
                <button
                  class={selectedTarget?.id === object.id
                    ? 'flex w-full items-center justify-between gap-3 bg-accent/10 px-3 py-2 text-left text-sm text-foreground'
                    : 'flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm text-muted-foreground hover:bg-muted/45 hover:text-foreground'}
                  type="button"
                  onclick={() => (selectedTarget = object)}
                >
                  <span class="truncate">{object.title}</span>
                  <span class="text-xs uppercase">{object.type}</span>
                </button>
              {:else}
                <p class="px-3 py-2 text-sm text-muted-foreground">
                  No matches.
                </p>
              {/each}
            </div>
          </div>
          <button
            class="h-10 rounded-md bg-accent px-4 text-sm font-medium text-accent-foreground disabled:opacity-45"
            type="button"
            disabled={!selectedTarget}
            onclick={confirmCreate}
          >
            Create
          </button>
        </div>
      </section>
    {/if}

    {#if message}
      <p class="border-b border-border px-5 py-3 text-sm text-muted-foreground">
        {message}
      </p>
    {/if}

    {#if selected && connections}
      {#if viewMode === 'list'}
        <StructureView
          current={selected}
          groups={structureGroups}
          {relationDefinitions}
          onSelectObject={selectObject}
        />
      {:else}
        <GraphView
          graph={localGraph}
          current={selected}
          depth={graphDepth}
          {relationDefinitions}
          onDepthChange={(depth) => (graphDepth = depth)}
          onSelectObject={selectObject}
        />
      {/if}
    {:else}
      <p class="p-5 text-sm text-muted-foreground">
        Select an object to explore its knowledge graph.
      </p>
    {/if}
  </main>

  <ConnectionsDetailsPanel
    object={selected}
    outgoing={filteredOutgoing}
    incoming={filteredIncoming}
    {relationDefinitions}
    onSelectObject={selectObject}
    onDeleteConnection={removeConnection}
  />
</section>

<style>
  .map-system {
    position: relative;
    background: hsl(var(--background));
  }

  .map-system::before {
    content: '';
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-image:
      linear-gradient(hsl(var(--foreground) / 0.024) 1px, transparent 1px),
      linear-gradient(90deg, hsl(var(--foreground) / 0.024) 1px, transparent 1px);
    background-size: 32px 32px;
  }

  .map-index,
  .map-canvas {
    position: relative;
    z-index: 1;
  }

  .map-core {
    display: inline-flex;
    width: 38px;
    height: 38px;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    border: 1px solid hsl(var(--accent) / 0.42);
    border-radius: 7px;
    color: hsl(var(--accent));
    background:
      linear-gradient(hsl(var(--foreground) / 0.05) 1px, transparent 1px),
      linear-gradient(90deg, hsl(var(--foreground) / 0.05) 1px, transparent 1px),
      hsl(var(--muted) / 0.22);
    background-size: 7px 7px;
  }

  .map-count {
    display: inline-flex;
    min-width: 28px;
    height: 26px;
    margin-left: auto;
    align-items: center;
    justify-content: center;
    border-left: 1px solid hsl(var(--border));
    color: hsl(var(--foreground));
    font-size: 0.7rem;
    font-weight: 700;
  }

  .map-object-list {
    position: relative;
  }

  .map-object-list::before {
    content: '';
    position: absolute;
    bottom: 10px;
    left: 19px;
    top: 10px;
    width: 1px;
    background: hsl(var(--border));
  }

  .map-object {
    position: relative;
    border-block: 1px solid transparent;
  }

  .map-object :global(svg) {
    position: relative;
    z-index: 1;
  }

  .map-object--active {
    border-color: hsl(var(--accent) / 0.38);
    background: hsl(var(--accent) / 0.075);
  }

  .map-object--active::after {
    content: '';
    position: absolute;
    right: 8px;
    top: 50%;
    width: 6px;
    height: 6px;
    transform: translateY(-50%);
    background: hsl(var(--accent));
    box-shadow: 0 0 8px hsl(var(--accent) / 0.55);
  }

  .map-toolbar {
    position: relative;
    background: hsl(var(--background) / 0.94);
  }

  .map-toolbar::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    width: 18%;
    height: 1px;
    background: hsl(var(--accent) / 0.62);
  }

  @media (max-width: 1279px) {
    .map-index {
      max-height: 340px;
    }
  }
</style>
