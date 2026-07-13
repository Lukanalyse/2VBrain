<script lang="ts">
  import { ArrowLeft, BookOpen, FileText } from '@lucide/svelte';

  import type { KnowledgeItem } from '$lib/features/knowledge/types/knowledge';

  export let item: KnowledgeItem;
</script>

<aside
  class="border-b border-border bg-background/55 p-4 lg:w-64 lg:border-b-0 lg:border-r"
>
  <a
    class="inline-flex h-9 items-center gap-2 rounded-md border border-border bg-muted/25 px-3 text-sm text-muted-foreground transition hover:text-foreground"
    href="/library"
  >
    <ArrowLeft size={15} />
    Library
  </a>

  <div class="mt-6 rounded-lg border border-border bg-muted/20 p-3">
    <div class="flex items-center gap-2 text-sm font-medium text-foreground">
      <BookOpen size={16} class="text-accent" />
      Knowledge Workspace
    </div>
    <p class="mt-2 line-clamp-3 text-xs leading-5 text-muted-foreground">
      {item.filename}
    </p>
  </div>

  <nav class="mt-6 space-y-1">
    <a
      class="flex h-9 items-center gap-2 rounded-md bg-muted px-3 text-sm text-foreground"
      href="#notes"
    >
      <FileText size={15} />
      Notes
    </a>
  </nav>
</aside>
