<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';

  onMount(() => {
    const objectId = `paper:${$page.params.id}`;
    void goto(`/workspace?open=${encodeURIComponent(objectId)}`, { replaceState: true });
  });
</script>

<p class="p-6 text-sm text-muted-foreground">Opening in Workspace...</p>
