<script lang="ts">
  import { page } from '$app/stores';

  import ConceptDetailPage from '$lib/features/concepts/ConceptDetailPage.svelte';

  $: slug = $page.params.slug ?? '';
</script>

<ConceptDetailPage {slug} />
