<script lang="ts">
  import { Cpu, Minus, Plus, RotateCcw, ZoomIn, ZoomOut } from '@lucide/svelte';

  import { entityMeta } from '$lib/design/entities';
  import type { LinkableObject } from '$lib/features/linking/types/linking';
  import type {
    ConnectionType,
    ConnectionTypeDefinition
  } from '$lib/features/connections/types/connections';
  import type {
    LocalGraph,
    LocalGraphNode
  } from '$lib/features/connections/types/knowledgeGraph';

  type PositionedNode = LocalGraphNode & {
    x: number;
    y: number;
    width: number;
    height: number;
  };

  type Props = {
    graph: LocalGraph;
    current: LinkableObject;
    depth: number;
    relationDefinitions: ConnectionTypeDefinition[];
    onDepthChange: (depth: number) => void;
    onSelectObject: (object: LinkableObject) => void;
  };

  let {
    graph,
    current,
    depth,
    relationDefinitions,
    onDepthChange,
    onSelectObject
  }: Props = $props();

  const width = 980;
  const height = 660;
  const corePinOffsets = [-48, -24, 0, 24, 48];
  let zoom = $state(1);
  let panX = $state(0);
  let panY = $state(0);
  let dragStart = $state<{
    x: number;
    y: number;
    panX: number;
    panY: number;
  } | null>(null);

  const relationById = $derived(
    Object.fromEntries(
      relationDefinitions.map((item) => [item.id, item])
    ) as Record<ConnectionType, ConnectionTypeDefinition>
  );

  const positionedNodes = $derived.by(() => {
    const center = { x: width / 2, y: height / 2 };
    const sorted = graph.nodes
      .slice()
      .sort((a, b) => a.depth - b.depth || b.relation_count - a.relation_count);
    const rings = new Map<number, LocalGraphNode[]>();
    for (const node of sorted) {
      rings.set(node.depth, [...(rings.get(node.depth) ?? []), node]);
    }

    return sorted.map((node): PositionedNode => {
      if (node.id === current.id || node.depth === 0) {
        return {
          ...node,
          x: center.x,
          y: center.y,
          width: 158,
          height: 96
        };
      }
      const ring = rings.get(node.depth) ?? [];
      const index = ring.findIndex((item) => item.id === node.id);
      const angle =
        (Math.PI * 2 * index) / Math.max(ring.length, 1) - Math.PI / 2;
      const ringRadius = 215 + (node.depth - 1) * 145;
      return {
        ...node,
        x: center.x + Math.cos(angle) * ringRadius,
        y: center.y + Math.sin(angle) * ringRadius,
        width: 126,
        height: 70
      };
    });
  });

  const nodeById = $derived(
    new Map<string, PositionedNode>(
      positionedNodes.map((node) => [node.id, node])
    )
  );

  function resetView(): void {
    zoom = 1;
    panX = 0;
    panY = 0;
  }

  function startDrag(event: PointerEvent): void {
    dragStart = { x: event.clientX, y: event.clientY, panX, panY };
  }

  function drag(event: PointerEvent): void {
    if (!dragStart) return;
    panX = dragStart.panX + event.clientX - dragStart.x;
    panY = dragStart.panY + event.clientY - dragStart.y;
  }

  function edgePath(source: PositionedNode, target: PositionedNode): string {
    const middleX = (source.x + target.x) / 2;
    return `M ${source.x} ${source.y} H ${middleX} V ${target.y} H ${target.x}`;
  }

  function shortTitle(value: string, limit: number): string {
    return value.length > limit ? `${value.slice(0, limit - 3)}...` : value;
  }
</script>

<section class="graph-shell flex min-h-0 flex-1 flex-col overflow-hidden px-4 pb-4">
  <div class="graph-heading flex flex-wrap items-center justify-between gap-3 py-3">
    <div class="flex min-w-0 items-center gap-3">
      <span class="graph-core-mark" aria-hidden="true">
        <Cpu size={16} />
      </span>
      <div class="min-w-0">
        <p class="text-[0.66rem] font-semibold uppercase text-accent">Neural graph</p>
        <h2 class="mt-0.5 truncate text-lg font-semibold text-foreground">
          {current.title}
        </h2>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <div class="depth-control flex h-9 items-center rounded-md border border-border bg-background/80">
        <button
          class="ros-btn-ghost h-8 w-8 justify-center px-0"
          type="button"
          aria-label="Decrease graph depth"
          onclick={() => onDepthChange(Math.max(1, depth - 1))}
        >
          <Minus size={13} />
        </button>
        <span class="border-inline flex h-5 items-center gap-2 border-x border-border px-2 text-[0.66rem] text-muted-foreground">
          Depth <strong class="text-foreground">{depth}</strong>
        </span>
        <button
          class="ros-btn-ghost h-8 w-8 justify-center px-0"
          type="button"
          aria-label="Increase graph depth"
          onclick={() => onDepthChange(Math.min(3, depth + 1))}
        >
          <Plus size={13} />
        </button>
      </div>
      <button
        class="ros-btn-icon"
        type="button"
        aria-label="Zoom out"
        title="Zoom out"
        onclick={() => (zoom = Math.max(0.65, zoom - 0.15))}
      >
        <ZoomOut size={15} />
      </button>
      <button
        class="ros-btn-icon"
        type="button"
        aria-label="Zoom in"
        title="Zoom in"
        onclick={() => (zoom = Math.min(1.8, zoom + 0.15))}
      >
        <ZoomIn size={15} />
      </button>
      <button
        class="ros-btn-icon"
        type="button"
        aria-label="Reset graph view"
        title="Reset graph view"
        onclick={resetView}
      >
        <RotateCcw size={15} />
      </button>
    </div>
  </div>

  <div class="graph-viewport min-h-[500px] flex-1 overflow-hidden border border-border">
    <svg
      class="h-full w-full touch-none"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Local knowledge graph"
      onpointerdown={startDrag}
      onpointermove={drag}
      onpointerup={() => (dragStart = null)}
      onpointerleave={() => (dragStart = null)}
    >
      <defs>
        <pattern id="neural-grid" width="28" height="28" patternUnits="userSpaceOnUse">
          <path d="M 28 0 L 0 0 0 28" class="graph-grid-line"></path>
        </pattern>
        <filter id="core-glow" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="4" result="blur"></feGaussianBlur>
          <feMerge>
            <feMergeNode in="blur"></feMergeNode>
            <feMergeNode in="SourceGraphic"></feMergeNode>
          </feMerge>
        </filter>
      </defs>

      <rect width={width} height={height} fill="url(#neural-grid)"></rect>

      <g transform={`translate(${panX} ${panY}) scale(${zoom})`}>
        {#each graph.edges as edge, index}
          {@const source = nodeById.get(edge.source_id)}
          {@const target = nodeById.get(edge.target_id)}
          {#if source && target}
            {@const path = edgePath(source, target)}
            <path d={path} class="circuit-edge"></path>
            <path
              d={path}
              class="circuit-signal"
              style={`animation-delay: ${index * -240}ms`}
            ></path>
            <text
              x={(source.x + target.x) / 2}
              y={(source.y + target.y) / 2 - 9}
              text-anchor="middle"
              class="relation-label"
            >
              {relationById[edge.relation_type]?.label}
            </text>
          {/if}
        {/each}

        {#each positionedNodes as node}
          {@const meta = entityMeta[node.type]}
          {@const isCurrent = node.id === current.id || node.depth === 0}
          <g
            role="button"
            tabindex="0"
            class:is-current={isCurrent}
            class="graph-node cursor-pointer"
            transform={`translate(${node.x} ${node.y})`}
            onclick={() => onSelectObject(node)}
            onkeydown={(event) => {
              if (event.key === 'Enter' || event.key === ' ')
                onSelectObject(node);
            }}
          >
            {#if isCurrent}
              {#each corePinOffsets as offset}
                <line x1={offset} y1={-node.height / 2 - 10} x2={offset} y2={-node.height / 2} class="chip-pin"></line>
                <line x1={offset} y1={node.height / 2} x2={offset} y2={node.height / 2 + 10} class="chip-pin"></line>
                <line x1={-node.width / 2 - 10} y1={offset * 0.62} x2={-node.width / 2} y2={offset * 0.62} class="chip-pin"></line>
                <line x1={node.width / 2} y1={offset * 0.62} x2={node.width / 2 + 10} y2={offset * 0.62} class="chip-pin"></line>
              {/each}
            {/if}

            <rect
              x={-node.width / 2}
              y={-node.height / 2}
              width={node.width}
              height={node.height}
              rx="8"
              class="node-body"
              fill="hsl(var(--background))"
              stroke={meta.colorVar}
              stroke-width={isCurrent ? '2.5' : '1.5'}
              filter={isCurrent ? 'url(#core-glow)' : undefined}
            ></rect>
            <rect
              x={-node.width / 2 + 7}
              y={-node.height / 2 + 7}
              width={node.width - 14}
              height={node.height - 14}
              rx="5"
              fill={meta.colorVar}
              fill-opacity={isCurrent ? '0.11' : '0.065'}
              stroke={meta.colorVar}
              stroke-opacity="0.24"
            ></rect>
            <rect
              x={-node.width / 2 + 11}
              y={-node.height / 2 + 11}
              width="5"
              height="5"
              fill={meta.colorVar}
              class="node-status-light"
            ></rect>
            <text
              y={isCurrent ? -19 : -12}
              text-anchor="middle"
              fill={meta.colorVar}
              class="node-type"
            >
              {isCurrent ? `CORE · ${node.type}` : node.type}
            </text>
            <text
              y={isCurrent ? 4 : 7}
              text-anchor="middle"
              class="node-title"
            >
              {shortTitle(node.title, isCurrent ? 24 : 18)}
            </text>
            {#if isCurrent}
              <text y="25" text-anchor="middle" class="node-meta">
                {node.relation_count} linked signals
              </text>
            {/if}
          </g>
        {/each}
      </g>
    </svg>
  </div>
</section>

<style>
  .graph-shell {
    background: hsl(var(--background) / 0.76);
  }

  .graph-heading {
    position: relative;
    border-bottom: 1px solid hsl(var(--border));
  }

  .graph-heading::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    width: 120px;
    height: 1px;
    background: hsl(var(--accent) / 0.65);
  }

  .graph-core-mark {
    display: inline-flex;
    width: 34px;
    height: 34px;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    border: 1px solid hsl(var(--accent) / 0.42);
    border-radius: 7px;
    color: hsl(var(--accent));
    background: hsl(var(--muted) / 0.18);
  }

  .graph-viewport {
    position: relative;
    border-radius: 8px;
    background: hsl(var(--background) / 0.9);
    box-shadow: inset 0 0 70px hsl(var(--accent) / 0.018);
    cursor: grab;
  }

  .graph-viewport:active {
    cursor: grabbing;
  }

  .graph-grid-line {
    fill: none;
    stroke: hsl(var(--foreground) / 0.035);
    stroke-width: 1;
  }

  .circuit-edge,
  .circuit-signal {
    fill: none;
    vector-effect: non-scaling-stroke;
  }

  .circuit-edge {
    stroke: hsl(var(--border));
    stroke-width: 1.5;
  }

  .circuit-signal {
    stroke: hsl(var(--accent) / 0.82);
    stroke-width: 1.8;
    stroke-dasharray: 2 26;
    stroke-linecap: square;
    animation: signal-flow 1.4s linear infinite;
  }

  .relation-label {
    fill: hsl(var(--muted-foreground));
    font-size: 9px;
  }

  .chip-pin {
    stroke: hsl(var(--muted-foreground) / 0.72);
    stroke-width: 3;
    vector-effect: non-scaling-stroke;
  }

  .node-body {
    transition:
      stroke-width 160ms ease,
      transform 160ms ease;
  }

  .graph-node:hover .node-body,
  .graph-node:focus-visible .node-body {
    stroke-width: 3;
  }

  .graph-node:focus-visible {
    outline: none;
  }

  .node-status-light {
    filter: drop-shadow(0 0 4px hsl(var(--accent) / 0.6));
  }

  .node-type {
    font-size: 8px;
    font-weight: 700;
    text-transform: uppercase;
  }

  .node-title {
    fill: hsl(var(--foreground));
    font-size: 11px;
    font-weight: 650;
  }

  .node-meta {
    fill: hsl(var(--muted-foreground));
    font-size: 8px;
  }

  @keyframes signal-flow {
    to { stroke-dashoffset: -56; }
  }

  @media (prefers-reduced-motion: reduce) {
    .circuit-signal {
      animation: none;
    }
  }
</style>
