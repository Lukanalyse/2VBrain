<script lang="ts" module>
  export type ProjectBrainHubTarget =
    | 'papers'
    | 'notes'
    | 'graph'
    | 'ideas'
    | 'brief';
</script>

<script lang="ts">
  import {
    BookOpen,
    FileText,
    GitBranch,
    Lightbulb,
    PenLine
  } from '@lucide/svelte';
  import type { Component } from 'svelte';

  import NeuralCore from '$lib/components/NeuralCore.svelte';
  import { entityMeta } from '$lib/design/entities';

  type HubNode = {
    id: ProjectBrainHubTarget;
    label: string;
    caption: string;
    count: number;
    icon: Component;
    className: string;
  };

  type Props = {
    paperCount: number;
    noteCount: number;
    conceptCount: number;
    ideaCount: number;
    reviewCount: number;
    relationCount: number;
    onSelect: (target: ProjectBrainHubTarget) => void;
  };

  let {
    paperCount,
    noteCount,
    conceptCount,
    ideaCount,
    reviewCount,
    relationCount,
    onSelect
  }: Props = $props();

  let activeTarget = $state<ProjectBrainHubTarget | null>(null);

  let nodes = $derived<HubNode[]>([
    {
      id: 'papers',
      label: 'Papers',
      caption: 'Corpus',
      count: paperCount,
      icon: BookOpen,
      className: entityMeta.paper.text
    },
    {
      id: 'notes',
      label: 'Notes',
      caption: 'Reading notes',
      count: noteCount,
      icon: FileText,
      className: entityMeta.note.text
    },
    {
      id: 'graph',
      label: 'Graph',
      caption: 'Concepts & links',
      count: relationCount,
      icon: GitBranch,
      className: entityMeta.concept.text
    },
    {
      id: 'ideas',
      label: 'Ideas',
      caption: 'Brainstorms',
      count: ideaCount,
      icon: Lightbulb,
      className: entityMeta.brainstorm.text
    },
    {
      id: 'brief',
      label: 'Brief',
      caption: 'Project note',
      count: reviewCount + conceptCount,
      icon: PenLine,
      className: entityMeta.project.text
    }
  ]);

  function select(target: ProjectBrainHubTarget): void {
    activeTarget = target;
    onSelect(target);
  }
</script>

<section class="project-hub" aria-label="Project navigation hub">
  <div class="project-grid" aria-hidden="true"></div>
  <div class="project-stage">
    <svg class="project-wires" viewBox="0 0 940 370" aria-hidden="true">
      <path
        class:wire-active={activeTarget === 'papers'}
        d="M 392 150 H 330 L 278 92 H 220"
      ></path>
      <path
        class:wire-active={activeTarget === 'notes'}
        d="M 392 220 H 330 L 278 282 H 220"
      ></path>
      <path
        class:wire-active={activeTarget === 'graph'}
        d="M 548 132 H 610 L 662 67 H 720"
      ></path>
      <path
        class:wire-active={activeTarget === 'ideas'}
        d="M 548 185 H 720"
      ></path>
      <path
        class:wire-active={activeTarget === 'brief'}
        d="M 548 238 H 610 L 662 303 H 720"
      ></path>
      <circle cx="220" cy="92" r="4"></circle>
      <circle cx="220" cy="282" r="4"></circle>
      <circle cx="720" cy="67" r="4"></circle>
      <circle cx="720" cy="185" r="4"></circle>
      <circle cx="720" cy="303" r="4"></circle>
    </svg>

    <div class="project-core">
      <NeuralCore
        compact
        label="Project Core"
        detail={`${relationCount} linked signals`}
      />
    </div>

    {#each nodes as node}
      {@const Icon = node.icon}
      <button
        class={`project-node project-node--${node.id}`}
        type="button"
        onclick={() => select(node.id)}
        onpointerenter={() => (activeTarget = node.id)}
        onpointerleave={() => (activeTarget = null)}
        onfocus={() => (activeTarget = node.id)}
        onblur={() => (activeTarget = null)}
      >
        <span class="node-terminal" aria-hidden="true"></span>
        <span class={`node-icon ${node.className}`}>
          <Icon size={17} strokeWidth={1.75} />
        </span>
        <span class="node-copy">
          <span class="node-label">{node.label}</span>
          <span class="node-caption">{node.caption}</span>
        </span>
        <span class="node-count">{node.count}</span>
      </button>
    {/each}
  </div>
</section>

<style>
  .project-hub {
    position: relative;
    margin: 18px 24px 0;
    overflow: hidden;
    border-block: 1px solid hsl(var(--border));
    background: hsl(var(--muted) / 0.055);
  }

  .project-grid {
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-image:
      linear-gradient(hsl(var(--foreground) / 0.03) 1px, transparent 1px),
      linear-gradient(90deg, hsl(var(--foreground) / 0.03) 1px, transparent 1px);
    background-size: 24px 24px;
    mask-image: linear-gradient(90deg, transparent, black 20%, black 80%, transparent);
  }

  .project-stage {
    position: relative;
    width: min(100%, 940px);
    height: 370px;
    margin: 0 auto;
  }

  .project-wires {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
  }

  .project-wires path {
    fill: none;
    stroke: hsl(var(--border));
    stroke-width: 1.3;
    stroke-dasharray: 4 6;
    vector-effect: non-scaling-stroke;
    transition: stroke 160ms ease;
  }

  .project-wires path.wire-active {
    stroke: hsl(var(--accent) / 0.82);
    animation: project-wire-flow 800ms linear infinite;
  }

  .project-wires circle {
    fill: hsl(var(--background));
    stroke: hsl(var(--accent) / 0.5);
    stroke-width: 1.4;
    vector-effect: non-scaling-stroke;
  }

  .project-core {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
  }

  .project-node {
    position: absolute;
    display: flex;
    width: 218px;
    min-height: 60px;
    align-items: center;
    gap: 10px;
    border-block: 1px solid hsl(var(--border));
    background: transparent;
    padding: 7px 5px;
    text-align: left;
    transition:
      border-color 160ms ease,
      background 160ms ease,
      transform 160ms ease;
  }

  .project-node:hover,
  .project-node:focus-visible {
    border-color: hsl(var(--accent) / 0.52);
    background: hsl(var(--muted) / 0.18);
    outline: none;
  }

  .project-node--papers {
    left: 0;
    top: 62px;
  }

  .project-node--notes {
    bottom: 57px;
    left: 0;
  }

  .project-node--graph {
    right: 0;
    top: 37px;
  }

  .project-node--ideas {
    right: 0;
    top: 155px;
  }

  .project-node--brief {
    bottom: 37px;
    right: 0;
  }

  .node-terminal {
    position: absolute;
    top: 50%;
    width: 8px;
    height: 8px;
    transform: translateY(-50%);
    border: 1px solid hsl(var(--accent) / 0.52);
    background: hsl(var(--background));
  }

  .project-node--papers .node-terminal,
  .project-node--notes .node-terminal {
    right: -12px;
  }

  .project-node--graph .node-terminal,
  .project-node--ideas .node-terminal,
  .project-node--brief .node-terminal {
    left: -12px;
  }

  .node-icon {
    display: inline-flex;
    width: 32px;
    height: 32px;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    border: 1px solid hsl(var(--border));
    border-radius: 7px;
    background: hsl(var(--background) / 0.72);
  }

  .node-copy {
    min-width: 0;
  }

  .node-label,
  .node-caption {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .node-label {
    color: hsl(var(--foreground));
    font-size: 0.82rem;
    font-weight: 650;
  }

  .node-caption {
    margin-top: 2px;
    color: hsl(var(--muted-foreground));
    font-size: 0.65rem;
  }

  .node-count {
    display: inline-flex;
    min-width: 26px;
    height: 24px;
    margin-left: auto;
    align-items: center;
    justify-content: center;
    border-left: 1px solid hsl(var(--border));
    color: hsl(var(--foreground));
    font-size: 0.7rem;
    font-weight: 700;
  }

  @keyframes project-wire-flow {
    to { stroke-dashoffset: -20; }
  }

  @media (max-width: 900px) {
    .project-hub {
      margin-inline: 16px;
      padding: 12px 0 16px;
    }

    .project-stage {
      display: grid;
      height: auto;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }

    .project-wires,
    .node-terminal {
      display: none;
    }

    .project-core {
      position: relative;
      left: auto;
      top: auto;
      display: flex;
      grid-column: 1 / -1;
      min-height: 210px;
      transform: none;
      align-items: center;
      justify-content: center;
    }

    .project-node {
      position: relative;
      inset: auto;
      width: 100%;
    }

    .project-node--brief {
      grid-column: 1 / -1;
    }
  }

  @media (max-width: 560px) {
    .project-stage {
      grid-template-columns: 1fr;
    }

    .project-node--brief {
      grid-column: auto;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .project-wires path.wire-active {
      animation: none;
    }
  }
</style>
