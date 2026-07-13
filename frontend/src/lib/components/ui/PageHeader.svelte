<script lang="ts">
  export let eyebrow = '';
  export let title: string;
  export let description = '';
  export let compact = false;
</script>

<div class="border-b border-border pb-5">
  {#if eyebrow}
    <p class="text-xs font-medium uppercase text-accent">{eyebrow}</p>
  {/if}
  <h1
    class={compact
      ? 'mt-2 text-2xl font-semibold text-foreground'
      : 'mt-2 text-3xl font-semibold text-foreground'}
  >
    {title}
  </h1>
  {#if description}
    <p class="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
      {description}
    </p>
  {/if}
  <slot />
</div>
