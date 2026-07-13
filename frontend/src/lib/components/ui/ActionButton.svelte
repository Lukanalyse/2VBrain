<script lang="ts">
  import type { Component } from 'svelte';

  import { cn } from '$lib/utils';

  export let icon: Component;
  export let label: string;
  export let meta: string | undefined = undefined;
  export let className = '';
</script>

<button
  class={cn(
    'group flex w-full items-center gap-3 rounded-md border border-border bg-background/45 px-3 py-3 text-left transition hover:border-accent/45 hover:bg-muted/55',
    className
  )}
  type="button"
>
  <span
    class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-border bg-muted/60 text-accent transition group-hover:border-accent/45"
  >
    <svelte:component this={icon} size={17} strokeWidth={1.8} />
  </span>
  <span class="min-w-0">
    <span class="block truncate text-sm font-medium text-foreground"
      >{label}</span
    >
    {#if meta}
      <span class="mt-0.5 block truncate text-xs text-muted-foreground"
        >{meta}</span
      >
    {/if}
  </span>
</button>
