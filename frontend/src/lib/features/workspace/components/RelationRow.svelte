<script lang="ts">
  import type { Snippet } from 'svelte';

  import { entityMeta } from '$lib/design/entities';
  import type { LinkableObject } from '$lib/features/linking/types/linking';

  type Props = {
    object: LinkableObject;
    onclick?: () => void;
    trailing?: Snippet;
  };

  let { object, onclick, trailing }: Props = $props();

  let meta = $derived(entityMeta[object.type]);
  let Icon = $derived(meta.icon);
</script>

<button type="button" class={`ros-row ${meta.borderLeft}`} {onclick}>
  <Icon size={15} class={`shrink-0 ${meta.text}`} />
  <span class="min-w-0 flex-1">
    <span class="block truncate text-sm leading-tight text-foreground"
      >{object.title}</span
    >
    {#if object.subtitle}
      <span class="mt-0.5 block truncate text-xs leading-tight text-muted-foreground"
        >{object.subtitle}</span
      >
    {/if}
  </span>
  {#if trailing}
    <span class="shrink-0 text-muted-foreground">{@render trailing()}</span>
  {/if}
</button>
