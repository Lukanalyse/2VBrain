<script lang="ts">
  import { Brain, Cpu } from '@lucide/svelte';

  type Props = {
    label?: string;
    detail?: string;
    compact?: boolean;
  };

  let {
    label = 'Research Core',
    detail = 'Systems online',
    compact = false
  }: Props = $props();
</script>

<div
  class={compact ? 'neural-core neural-core--compact' : 'neural-core'}
  aria-label={label}
  role="img"
>
  <div class="core-field" aria-hidden="true">
    <span class="field-ring field-ring--outer"></span>
    <span class="field-ring field-ring--inner"></span>
    <span class="field-axis field-axis--horizontal"></span>
    <span class="field-axis field-axis--vertical"></span>
  </div>

  <div class="processor-shell">
    <div class="pin-row pin-row--top" aria-hidden="true">
      {#each Array(8) as _}<span></span>{/each}
    </div>
    <div class="pin-row pin-row--bottom" aria-hidden="true">
      {#each Array(8) as _}<span></span>{/each}
    </div>
    <div class="pin-column pin-column--left" aria-hidden="true">
      {#each Array(8) as _}<span></span>{/each}
    </div>
    <div class="pin-column pin-column--right" aria-hidden="true">
      {#each Array(8) as _}<span></span>{/each}
    </div>

    <div class="processor-body">
      <div class="processor-grid" aria-hidden="true"></div>
      <span class="corner-light corner-light--one" aria-hidden="true"></span>
      <span class="corner-light corner-light--two" aria-hidden="true"></span>
      <span class="corner-light corner-light--three" aria-hidden="true"></span>
      <span class="corner-light corner-light--four" aria-hidden="true"></span>
      <span class="scan-line" aria-hidden="true"></span>

      <div class="brain-module">
        <span class="brain-signal" aria-hidden="true"></span>
        <Brain class="brain-icon" strokeWidth={1.55} />
      </div>

      <div class="processor-label">
        <Cpu size={compact ? 10 : 12} strokeWidth={1.8} />
        <span>{label}</span>
      </div>
      <span class="processor-detail">{detail}</span>
    </div>
  </div>
</div>

<style>
  .neural-core {
    --core-size: 244px;
    --chip-size: 164px;
    position: relative;
    display: grid;
    width: var(--core-size);
    aspect-ratio: 1;
    place-items: center;
    perspective: 800px;
  }

  .neural-core--compact {
    --core-size: 198px;
    --chip-size: 132px;
  }

  .core-field,
  .processor-shell {
    position: absolute;
    inset: 0;
  }

  .core-field {
    pointer-events: none;
  }

  .field-ring {
    position: absolute;
    inset: 12%;
    border: 1px solid hsl(var(--accent) / 0.2);
    clip-path: polygon(16% 0, 84% 0, 100% 16%, 100% 84%, 84% 100%, 16% 100%, 0 84%, 0 16%);
  }

  .field-ring--outer {
    animation: core-field-pulse 3.6s ease-in-out infinite;
  }

  .field-ring--inner {
    inset: 21%;
    border-color: hsl(var(--entity-concept) / 0.34);
    animation: core-field-pulse 3.6s 1.8s ease-in-out infinite;
  }

  .field-ring::before,
  .field-ring::after {
    content: '';
    position: absolute;
    width: 5px;
    height: 5px;
    background: hsl(var(--accent));
    box-shadow: 0 0 10px hsl(var(--accent) / 0.65);
  }

  .field-ring::before {
    left: -3px;
    top: 34%;
  }

  .field-ring::after {
    bottom: 22%;
    right: -3px;
  }

  .field-axis {
    position: absolute;
    background: hsl(var(--accent) / 0.13);
  }

  .field-axis--horizontal {
    left: 2%;
    right: 2%;
    top: 50%;
    height: 1px;
  }

  .field-axis--vertical {
    bottom: 2%;
    left: 50%;
    top: 2%;
    width: 1px;
  }

  .processor-shell {
    display: grid;
    place-items: center;
    transform: rotateX(5deg) rotateZ(-2deg);
    transform-style: preserve-3d;
    transition: transform 240ms ease;
  }

  .neural-core:hover .processor-shell {
    transform: rotateX(1deg) rotateZ(0deg) translateY(-2px);
  }

  .processor-body {
    position: relative;
    display: flex;
    width: var(--chip-size);
    aspect-ratio: 1;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    border: 1px solid hsl(var(--accent) / 0.46);
    border-radius: 8px;
    background:
      linear-gradient(145deg, hsl(var(--muted) / 0.92), hsl(var(--background)) 68%),
      hsl(var(--background));
    box-shadow:
      inset 0 0 0 6px hsl(var(--foreground) / 0.025),
      inset 0 0 0 7px hsl(var(--border) / 0.7),
      0 22px 44px hsl(0 0% 0% / 0.36);
  }

  .processor-grid {
    position: absolute;
    inset: 15px;
    background-image:
      linear-gradient(hsl(var(--foreground) / 0.07) 1px, transparent 1px),
      linear-gradient(90deg, hsl(var(--foreground) / 0.07) 1px, transparent 1px);
    background-size: 10px 10px;
    mask-image: linear-gradient(to bottom, transparent, black 24%, black 76%, transparent);
  }

  .brain-module {
    position: relative;
    z-index: 2;
    display: grid;
    width: 56%;
    aspect-ratio: 1;
    place-items: center;
    border: 1px solid hsl(var(--entity-concept) / 0.48);
    border-radius: 8px;
    background: hsl(var(--background) / 0.86);
    box-shadow:
      inset 0 0 24px hsl(var(--entity-concept) / 0.1),
      0 0 28px hsl(var(--entity-concept) / 0.1);
  }

  :global(.brain-icon) {
    width: 64%;
    height: 64%;
    color: hsl(var(--entity-concept));
    filter: drop-shadow(0 0 7px hsl(var(--entity-concept) / 0.32));
  }

  .brain-signal {
    position: absolute;
    inset: 8px;
    border: 1px solid hsl(var(--entity-concept) / 0.2);
    border-radius: 6px;
    animation: brain-signal 2.8s ease-out infinite;
  }

  .processor-label {
    position: relative;
    z-index: 2;
    display: flex;
    margin-top: 10px;
    align-items: center;
    gap: 5px;
    color: hsl(var(--foreground));
    font-size: 0.68rem;
    font-weight: 700;
    line-height: 1;
  }

  .processor-detail {
    position: relative;
    z-index: 2;
    margin-top: 5px;
    color: hsl(var(--muted-foreground));
    font-size: 0.57rem;
    line-height: 1;
  }

  .neural-core--compact .processor-label {
    margin-top: 8px;
    font-size: 0.59rem;
  }

  .neural-core--compact .processor-detail {
    font-size: 0.5rem;
  }

  .scan-line {
    position: absolute;
    z-index: 1;
    left: 14px;
    right: 14px;
    top: 18%;
    height: 1px;
    background: hsl(var(--accent) / 0.5);
    box-shadow: 0 0 8px hsl(var(--accent) / 0.35);
    animation: processor-scan 3.2s ease-in-out infinite;
  }

  .corner-light {
    position: absolute;
    z-index: 3;
    width: 5px;
    height: 5px;
    background: hsl(var(--accent));
    box-shadow: 0 0 8px hsl(var(--accent) / 0.65);
  }

  .corner-light--one {
    left: 12px;
    top: 12px;
  }

  .corner-light--two {
    right: 12px;
    top: 12px;
    animation: status-blink 2.4s 0.8s ease-in-out infinite;
  }

  .corner-light--three {
    bottom: 12px;
    left: 12px;
    animation: status-blink 2.4s 1.4s ease-in-out infinite;
  }

  .corner-light--four {
    bottom: 12px;
    right: 12px;
  }

  .pin-row,
  .pin-column {
    position: absolute;
    z-index: -1;
    display: flex;
    justify-content: space-between;
  }

  .pin-row {
    left: calc((100% - var(--chip-size)) / 2 + 12px);
    width: calc(var(--chip-size) - 24px);
  }

  .pin-row--top {
    top: calc((100% - var(--chip-size)) / 2 - 10px);
  }

  .pin-row--bottom {
    bottom: calc((100% - var(--chip-size)) / 2 - 10px);
  }

  .pin-row span {
    width: 4px;
    height: 16px;
    border: 1px solid hsl(var(--border));
    background: hsl(var(--muted-foreground) / 0.55);
  }

  .pin-column {
    top: calc((100% - var(--chip-size)) / 2 + 12px);
    height: calc(var(--chip-size) - 24px);
    flex-direction: column;
  }

  .pin-column--left {
    left: calc((100% - var(--chip-size)) / 2 - 10px);
  }

  .pin-column--right {
    right: calc((100% - var(--chip-size)) / 2 - 10px);
  }

  .pin-column span {
    width: 16px;
    height: 4px;
    border: 1px solid hsl(var(--border));
    background: hsl(var(--muted-foreground) / 0.55);
  }

  @keyframes core-field-pulse {
    0%, 100% { opacity: 0.38; }
    50% { opacity: 0.9; }
  }

  @keyframes brain-signal {
    0% { opacity: 0.7; transform: scale(0.9); }
    70%, 100% { opacity: 0; transform: scale(1.12); }
  }

  @keyframes processor-scan {
    0%, 100% { top: 18%; opacity: 0.22; }
    50% { top: 82%; opacity: 0.72; }
  }

  @keyframes status-blink {
    0%, 62%, 100% { opacity: 1; }
    68%, 76% { opacity: 0.25; }
  }

  @media (prefers-reduced-motion: reduce) {
    .field-ring,
    .brain-signal,
    .scan-line,
    .corner-light {
      animation: none;
    }

    .processor-shell {
      transition: none;
    }
  }
</style>
