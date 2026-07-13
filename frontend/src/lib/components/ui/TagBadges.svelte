<script lang="ts">
  // Sober, theme-aware tag badges. Tags are not type-specific, so they use the
  // neutral muted palette (never an entity color) to stay calm across screens.
  type Props = {
    tags: string[] | undefined | null;
    class?: string;
  };

  let { tags, class: className = '' }: Props = $props();

  let list = $derived(
    (tags ?? []).map((tag) => tag.trim()).filter((tag) => tag.length > 0)
  );
</script>

{#if list.length}
  <div class={`flex flex-wrap items-center gap-1.5 ${className}`}>
    {#each list as tag}
      <span
        class="inline-flex items-center rounded-full border border-border/70 bg-muted/40 px-2 py-0.5 text-[11px] font-medium leading-none text-muted-foreground"
      >
        {tag}
      </span>
    {/each}
  </div>
{/if}
