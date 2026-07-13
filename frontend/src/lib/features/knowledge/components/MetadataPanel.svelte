<script lang="ts">
  import type { KnowledgeItem } from '$lib/features/knowledge/types/knowledge';

  export let item: KnowledgeItem;

  $: fields = [
    ['Title', item.title || item.filename],
    ['Authors', item.authors || 'Empty'],
    ['Journal', item.journal || 'Empty'],
    ['Conference', item.conference || 'Empty'],
    ['Year', item.year ? String(item.year) : 'Empty'],
    ['DOI', item.doi || 'Empty'],
    ['Keywords', item.keywords || 'Empty']
  ];
</script>

<div class="space-y-4 p-5">
  <div>
    <p class="text-xs font-medium uppercase text-accent">Metadata</p>
    <h2 class="mt-1 text-sm font-semibold text-foreground">Document index</h2>
  </div>

  <dl class="space-y-4">
    <div>
      <dt class="text-xs text-muted-foreground">Name</dt>
      <dd class="mt-1 break-words text-sm text-foreground">{item.filename}</dd>
    </div>
    <div>
      <dt class="text-xs text-muted-foreground">Status</dt>
      <dd class="mt-1 text-sm capitalize text-foreground">{item.status}</dd>
    </div>
    <div>
      <dt class="text-xs text-muted-foreground">PDF path</dt>
      <dd class="mt-1 break-words text-xs leading-5 text-foreground">
        {item.file_path}
      </dd>
    </div>
    <div>
      <dt class="text-xs text-muted-foreground">Markdown path</dt>
      <dd class="mt-1 break-words text-xs leading-5 text-foreground">
        {item.markdown_path}
      </dd>
    </div>
    {#each fields as [label, value]}
      <div>
        <dt class="text-xs text-muted-foreground">{label}</dt>
        <dd class="mt-1 break-words text-sm text-muted-foreground">{value}</dd>
      </div>
    {/each}
    <div>
      <dt class="text-xs text-muted-foreground">Abstract</dt>
      <dd class="mt-1 text-sm leading-6 text-muted-foreground">
        {item.abstract || 'Empty'}
      </dd>
    </div>
  </dl>
</div>
