<script lang="ts">
  export let eyebrow: string | undefined = undefined;
  export let title: string;
  export let description: string | undefined = undefined;
</script>

<div class="flex min-w-0 items-end justify-between gap-4">
  <div class="min-w-0">
    {#if eyebrow}
      <p class="text-xs font-medium uppercase text-accent">{eyebrow}</p>
    {/if}
    <h2 class="mt-1 text-base font-semibold text-foreground">{title}</h2>
    {#if description}
      <p class="mt-1 text-sm leading-6 text-muted-foreground">{description}</p>
    {/if}
  </div>
  <slot name="action" />
</div>
