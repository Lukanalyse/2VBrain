<script lang="ts">
  import type { Component } from 'svelte';

  export let icon: Component;
  export let title: string;
  export let description: string;
</script>

<section
  class="flex min-h-[calc(100vh-4rem)] items-center justify-center px-6 py-16"
>
  <div class="w-full max-w-md text-center">
    <div
      class="mx-auto flex h-12 w-12 items-center justify-center rounded-lg border border-border bg-muted/40 text-accent"
    >
      <svelte:component this={icon} size={20} strokeWidth={1.8} />
    </div>
    <h1 class="mt-5 text-2xl font-semibold text-foreground">{title}</h1>
    <p class="mt-3 text-sm leading-6 text-muted-foreground">{description}</p>
  </div>
</section>
