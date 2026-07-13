<script lang="ts">
  import { entityMeta } from '$lib/design/entities';
  import type { LinkableType } from '$lib/features/linking/types/linking';

  type Props = {
    type: LinkableType;
    size?: number;
    showLabel?: boolean;
  };

  let { type, size = 12, showLabel = true }: Props = $props();
  let meta = $derived(entityMeta[type]);
</script>

<span
  class={[
    'inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium',
    meta.badge
  ]}
>
  <meta.icon {size} strokeWidth={2} />
  {#if showLabel}<span>{meta.label}</span>{/if}
</span>
