<script lang="ts">
  import {
    ArrowRight,
    BrainCircuit,
    Library,
    Network,
    PanelsTopLeft
  } from '@lucide/svelte';
  import { onMount } from 'svelte';
  import type { Component } from 'svelte';

  import NeuralCore from '$lib/components/NeuralCore.svelte';
  import { entityMeta } from '$lib/design/entities';
  import type { LinkableObject } from '$lib/features/linking/types/linking';
  import {
    getHomeSummary,
    type HomeSummary
  } from '$lib/features/workspace/services/workspaceApi';

  type ModuleId = 'workspace' | 'assistant' | 'library' | 'map';
  type HubModule = {
    id: ModuleId;
    label: string;
    role: string;
    href: string;
    metric: string;
    icon: Component;
  };

  let summary = $state<HomeSummary | null>(null);
  let isLoading = $state(true);
  let errorMessage = $state<string | null>(null);
  let activeModule = $state<ModuleId | 'resume' | null>(null);

  let allActive = $derived(
    summary
      ? uniqueObjects([
          ...summary.projects,
          ...summary.continue_reading,
          ...summary.recent_brainstorm
        ]).slice(0, 6)
      : []
  );
  let primaryContinue = $derived(allActive[0] ?? null);
  let paperCount = $derived(summary?.recent_papers.length ?? 0);
  let conceptCount = $derived(summary?.recent_concepts.length ?? 0);
  let projectCount = $derived(summary?.projects.length ?? 0);
  let continueUrl = $derived(
    primaryContinue ? workspaceUrl(primaryContinue) : '/workspace'
  );
  let coreDetail = $derived(
    isLoading
      ? 'Synchronizing'
      : primaryContinue
        ? `${entityMeta[primaryContinue.type].label} ready`
        : 'Ready for first input'
  );

  let modules = $derived<HubModule[]>([
    {
      id: 'workspace',
      label: 'Workspace',
      role: 'Active desk',
      href: '/workspace',
      metric: `${allActive.length} active`,
      icon: PanelsTopLeft
    },
    {
      id: 'assistant',
      label: 'Assistant',
      role: 'Local intelligence',
      href:
        primaryContinue?.type === 'project'
          ? `/assistant?project=${encodeURIComponent(primaryContinue.id)}`
          : '/assistant',
      metric: `${projectCount} projects`,
      icon: BrainCircuit
    },
    {
      id: 'library',
      label: 'Library',
      role: 'Complete index',
      href: '/library',
      metric: `${paperCount} papers`,
      icon: Library
    },
    {
      id: 'map',
      label: 'Map',
      role: 'Relations',
      href: '/connections',
      metric: `${conceptCount} concepts`,
      icon: Network
    }
  ]);

  onMount(async () => {
    try {
      summary = await getHomeSummary();
    } catch (error) {
      errorMessage =
        error instanceof Error ? error.message : 'Unable to load the hub.';
    } finally {
      isLoading = false;
    }
  });

  function workspaceUrl(item: LinkableObject): string {
    return `/workspace?open=${encodeURIComponent(item.id)}`;
  }

  function uniqueObjects(items: LinkableObject[]): LinkableObject[] {
    const seen = new Set<string>();
    return items.filter((item) => {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });
  }
</script>

<section class="hub-page" aria-labelledby="hub-title">
  <div class="hub-grid" aria-hidden="true"></div>
  <div class="hub-glow" aria-hidden="true"></div>

  <header class="hub-heading">
    <div>
      <p class="hub-kicker">Cognitive operating system</p>
      <h1 id="hub-title">Research OS</h1>
    </div>
    <p>One core. Four dedicated spaces.</p>
  </header>

  <div class="hub-stage">
    <svg class="hub-circuits" viewBox="0 0 1120 560" aria-hidden="true">
      <path class:wire-active={activeModule === 'assistant'} d="M 560 218 V 92"
      ></path>
      <path
        class:wire-active={activeModule === 'workspace'}
        d="M 467 250 H 410 L 355 190 H 258 L 220 152 H 132"
      ></path>
      <path
        class:wire-active={activeModule === 'library'}
        d="M 653 250 H 710 L 765 190 H 862 L 900 152 H 988"
      ></path>
      <path
        class:wire-active={activeModule === 'resume'}
        d="M 467 310 H 405 L 348 400 H 250 L 218 442 H 132"
      ></path>
      <path
        class:wire-active={activeModule === 'map'}
        d="M 653 310 H 715 L 772 400 H 870 L 902 442 H 988"
      ></path>
      <circle cx="132" cy="152" r="5"></circle>
      <circle cx="560" cy="92" r="5"></circle>
      <circle cx="988" cy="152" r="5"></circle>
      <circle cx="132" cy="442" r="5"></circle>
      <circle cx="988" cy="442" r="5"></circle>
    </svg>

    <a
      class="core-entry"
      class:core-entry--active={activeModule !== null}
      href={continueUrl}
      onpointerenter={() => (activeModule = 'resume')}
      onpointerleave={() => (activeModule = null)}
      onfocus={() => (activeModule = 'resume')}
      onblur={() => (activeModule = null)}
      aria-label={primaryContinue
        ? `Continue ${primaryContinue.title}`
        : 'Enter Workspace'}
    >
      <NeuralCore label="Research Core" detail={coreDetail} />
      <span class="core-command">
        <span>
          <span class="command-label">
            {primaryContinue ? 'Continue' : 'Enter workspace'}
          </span>
          <span class="command-target">
            {primaryContinue?.title ?? 'Start a new thread'}
          </span>
        </span>
        <ArrowRight size={16} />
      </span>
    </a>

    {#each modules as module}
      {@const Icon = module.icon}
      <a
        class={`hub-module hub-module--${module.id}`}
        href={module.href}
        onpointerenter={() => (activeModule = module.id)}
        onpointerleave={() => (activeModule = null)}
        onfocus={() => (activeModule = module.id)}
        onblur={() => (activeModule = null)}
      >
        <span class="module-terminal" aria-hidden="true"></span>
        <span class="module-icon"><Icon size={19} strokeWidth={1.7} /></span>
        <span class="module-copy">
          <span class="module-role">{module.role}</span>
          <span class="module-label">{module.label}</span>
        </span>
        <span class="module-metric">{module.metric}</span>
        <ArrowRight class="module-arrow" size={15} />
      </a>
    {/each}

    <a
      class="resume-node"
      href={continueUrl}
      onpointerenter={() => (activeModule = 'resume')}
      onpointerleave={() => (activeModule = null)}
      onfocus={() => (activeModule = 'resume')}
      onblur={() => (activeModule = null)}
    >
      {#if primaryContinue}
        {@const MetaIcon = entityMeta[primaryContinue.type].icon}
        <span class={`resume-icon ${entityMeta[primaryContinue.type].text}`}>
          <MetaIcon size={17} />
        </span>
        <span class="min-w-0">
          <span class="resume-role">Current thread</span>
          <span class="resume-title">{primaryContinue.title}</span>
        </span>
      {:else}
        <span class="resume-icon text-entity-project">
          <PanelsTopLeft size={17} />
        </span>
        <span>
          <span class="resume-role">Current thread</span>
          <span class="resume-title">No active work</span>
        </span>
      {/if}
      <ArrowRight class="ml-auto shrink-0" size={15} />
    </a>
  </div>

  <footer class="hub-status">
    <span>
      <span class="status-light"></span>
      {errorMessage ?? (isLoading ? 'Core synchronizing' : 'Core online')}
    </span>
    <span>{projectCount} projects</span>
    <span>{paperCount} recent papers</span>
    <span>{conceptCount} concepts</span>
  </footer>
</section>

<style>
  .hub-page {
    position: relative;
    min-height: calc(100vh - 4rem);
    overflow: hidden;
    padding: 28px clamp(18px, 4vw, 56px) 24px;
    background: hsl(var(--background));
  }

  .hub-grid {
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-image:
      linear-gradient(hsl(var(--foreground) / 0.052) 1px, transparent 1px),
      linear-gradient(
        90deg,
        hsl(var(--foreground) / 0.052) 1px,
        transparent 1px
      );
    background-size: 32px 32px;
    mask-image: linear-gradient(to bottom, black, transparent 82%);
  }

  .hub-glow {
    position: absolute;
    left: 50%;
    top: 49%;
    width: min(58vw, 720px);
    height: min(42vw, 470px);
    transform: translate(-50%, -50%);
    border: 1px solid hsl(var(--accent) / 0.17);
    clip-path: polygon(
      12% 0,
      88% 0,
      100% 28%,
      100% 72%,
      88% 100%,
      12% 100%,
      0 72%,
      0 28%
    );
    box-shadow:
      inset 0 0 90px hsl(var(--accent) / 0.055),
      0 0 80px hsl(var(--accent) / 0.045);
  }

  .hub-heading {
    position: relative;
    z-index: 3;
    display: flex;
    max-width: 1180px;
    margin: 0 auto;
    align-items: end;
    justify-content: space-between;
    gap: 24px;
  }

  .hub-kicker {
    color: hsl(var(--accent));
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
  }

  .hub-heading h1 {
    margin: 5px 0 0;
    font-size: clamp(1.85rem, 3.2vw, 3rem);
    font-weight: 650;
    line-height: 1;
  }

  .hub-heading > p {
    margin: 0 0 3px;
    color: hsl(var(--muted-foreground));
    font-size: 0.78rem;
  }

  .hub-stage {
    position: relative;
    z-index: 2;
    width: min(100%, 1120px);
    height: clamp(470px, 66vh, 600px);
    min-height: 500px;
    margin: 4px auto 0;
  }

  .hub-circuits {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    overflow: visible;
  }

  .hub-circuits path {
    fill: none;
    stroke: hsl(var(--border) / 0.84);
    stroke-width: 1.4;
    stroke-dasharray: 5 7;
    vector-effect: non-scaling-stroke;
    transition:
      stroke 180ms ease,
      stroke-width 180ms ease;
  }

  .hub-circuits path.wire-active {
    stroke: hsl(var(--accent) / 0.82);
    stroke-width: 2;
    animation: circuit-flow 900ms linear infinite;
  }

  .hub-circuits circle {
    fill: hsl(var(--surface));
    stroke: hsl(var(--accent) / 0.62);
    stroke-width: 1.5;
    vector-effect: non-scaling-stroke;
  }

  .core-entry {
    position: absolute;
    left: 50%;
    top: 48%;
    display: flex;
    width: 264px;
    transform: translate(-50%, -50%);
    flex-direction: column;
    align-items: center;
    color: inherit;
    text-decoration: none;
  }

  .core-entry:focus-visible {
    outline: 2px solid hsl(var(--accent) / 0.7);
    outline-offset: 8px;
  }

  .core-command {
    position: relative;
    z-index: 4;
    display: flex;
    width: 224px;
    min-height: 48px;
    margin-top: -22px;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    border: 1px solid hsl(var(--border) / 0.95);
    border-radius: 7px;
    background: hsl(var(--surface-raised) / 0.97);
    padding: 7px 10px 7px 12px;
    box-shadow:
      inset 0 1px 0 hsl(var(--foreground) / 0.055),
      0 12px 28px hsl(0 0% 0% / 0.32);
    transition:
      border-color 180ms ease,
      transform 180ms ease;
  }

  .core-entry:hover .core-command,
  .core-entry--active .core-command {
    transform: translateY(-2px);
    border-color: hsl(var(--accent) / 0.56);
  }

  .command-label,
  .command-target {
    display: block;
    max-width: 174px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .command-label {
    color: hsl(var(--accent));
    font-size: 0.62rem;
    font-weight: 700;
    text-transform: uppercase;
  }

  .command-target {
    margin-top: 3px;
    color: hsl(var(--foreground));
    font-size: 0.76rem;
    font-weight: 600;
  }

  .hub-module,
  .resume-node {
    position: absolute;
    display: flex;
    width: 244px;
    min-height: 72px;
    align-items: center;
    gap: 12px;
    border-block: 1px solid hsl(var(--border) / 0.88);
    background: hsl(var(--surface) / 0.34);
    color: inherit;
    text-decoration: none;
    transition:
      border-color 180ms ease,
      background 180ms ease,
      transform 180ms ease;
  }

  .hub-module {
    padding: 9px 6px;
  }

  .hub-module:hover,
  .hub-module:focus-visible,
  .resume-node:hover,
  .resume-node:focus-visible {
    border-color: hsl(var(--accent) / 0.48);
    background: hsl(var(--surface-raised) / 0.62);
    outline: none;
  }

  .hub-module--workspace {
    left: 0;
    top: 14%;
  }

  .hub-module--assistant {
    left: 50%;
    top: 1%;
    transform: translateX(-50%);
  }

  .hub-module--library {
    right: 0;
    top: 14%;
  }

  .hub-module--map {
    bottom: 6%;
    right: 0;
  }

  .module-terminal {
    position: absolute;
    top: 50%;
    width: 9px;
    height: 9px;
    transform: translateY(-50%);
    border: 1px solid hsl(var(--accent) / 0.56);
    background: hsl(var(--surface));
  }

  .hub-module--workspace .module-terminal {
    right: -13px;
  }

  .hub-module--assistant .module-terminal {
    top: auto;
    bottom: -13px;
    left: 50%;
    transform: translateX(-50%);
  }

  .hub-module--library .module-terminal,
  .hub-module--map .module-terminal {
    left: -13px;
  }

  .module-icon,
  .resume-icon {
    display: inline-flex;
    width: 34px;
    height: 34px;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    border: 1px solid hsl(var(--border) / 0.9);
    border-radius: 7px;
    color: hsl(var(--accent));
    background: hsl(var(--surface-raised) / 0.78);
  }

  .module-copy {
    min-width: 0;
  }

  .module-role,
  .resume-role {
    display: block;
    color: hsl(var(--muted-foreground));
    font-size: 0.61rem;
    font-weight: 650;
    text-transform: uppercase;
  }

  .module-label,
  .resume-title {
    display: block;
    margin-top: 3px;
    overflow: hidden;
    color: hsl(var(--foreground));
    font-size: 0.9rem;
    font-weight: 650;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .module-metric {
    margin-left: auto;
    color: hsl(var(--muted-foreground));
    font-size: 0.66rem;
    white-space: nowrap;
  }

  :global(.module-arrow) {
    flex: 0 0 auto;
    color: hsl(var(--muted-foreground));
    transition: transform 180ms ease;
  }

  .hub-module:hover :global(.module-arrow) {
    transform: translateX(3px);
    color: hsl(var(--accent));
  }

  .resume-node {
    bottom: 6%;
    left: 0;
    padding: 9px 6px;
  }

  .hub-status {
    position: relative;
    z-index: 3;
    display: flex;
    width: min(100%, 1120px);
    min-height: 36px;
    margin: -6px auto 0;
    align-items: center;
    gap: 22px;
    border-top: 1px solid hsl(var(--border) / 0.9);
    color: hsl(var(--muted-foreground));
    font-size: 0.65rem;
  }

  .hub-status > span {
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }

  .hub-status > span:first-child {
    margin-right: auto;
  }

  .status-light {
    width: 5px;
    height: 5px;
    background: hsl(var(--accent));
    box-shadow: 0 0 8px hsl(var(--accent) / 0.62);
  }

  @keyframes circuit-flow {
    to {
      stroke-dashoffset: -24;
    }
  }

  @media (max-width: 840px) {
    .hub-page {
      padding: 22px 16px 28px;
    }

    .hub-heading {
      align-items: start;
    }

    .hub-heading > p {
      display: none;
    }

    .hub-stage {
      display: flex;
      height: auto;
      min-height: 0;
      margin-top: 14px;
      flex-direction: column;
      align-items: stretch;
      gap: 10px;
    }

    .hub-circuits,
    .hub-glow,
    .module-terminal {
      display: none;
    }

    .core-entry,
    .hub-module,
    .resume-node {
      position: relative;
      inset: auto;
      width: 100%;
      transform: none;
    }

    .core-entry {
      order: 0;
      min-height: 258px;
      justify-content: center;
    }

    .core-command {
      margin-top: -28px;
    }

    .hub-module {
      min-height: 62px;
      order: 3;
    }

    .hub-module--assistant {
      order: 1;
    }

    .resume-node {
      min-height: 62px;
      order: 2;
    }

    .hub-module:hover,
    .resume-node:hover {
      transform: none;
    }

    .hub-status {
      margin-top: 18px;
      padding-top: 12px;
      flex-wrap: wrap;
      gap: 9px 18px;
    }

    .hub-status > span:first-child {
      width: 100%;
      margin-right: 0;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .hub-circuits path.wire-active {
      animation: none;
    }
  }
</style>
