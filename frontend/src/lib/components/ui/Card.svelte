<script lang="ts">
  import { cn } from '$lib/utils';

  export let className = '';
</script>

<section
  class={cn(
    'rounded-lg border border-border bg-muted/25 shadow-panel',
    className
  )}
>
  <slot />
</section>
