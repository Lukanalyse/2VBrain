<script lang="ts">
  import type { WorkspacePanelContext } from '$lib/features/workspace/types/panels';

  type Props = {
    context: WorkspacePanelContext;
  };

  let { context }: Props = $props();
  let metadataEntries = $derived(
    Object.entries(context.detail?.metadata ?? {})
  );
</script>

<section class="grid gap-3">
  <div class="rounded-lg border border-border bg-muted/[0.08] p-3">
    <p class="text-xs font-medium uppercase text-muted-foreground">Object</p>
    <h3 class="mt-1 truncate text-sm font-semibold text-foreground">
      {context.object.title}
    </h3>
    <p class="mt-1 text-xs text-muted-foreground">{context.object.type}</p>
  </div>

  <div class="rounded-lg border border-border bg-muted/[0.08] p-3">
    <p class="text-xs font-medium uppercase text-muted-foreground">
      Vault Path
    </p>
    <p class="mt-2 break-words text-xs leading-5 text-muted-foreground">
      {context.object.markdown_path}
    </p>
  </div>

  {#if metadataEntries.length}
    <div class="rounded-lg border border-border bg-muted/[0.08] p-3">
      <p class="text-xs font-medium uppercase text-muted-foreground">
        Metadata
      </p>
      <dl class="mt-3 grid gap-2">
        {#each metadataEntries as [key, value]}
          <div>
            <dt class="text-[0.68rem] uppercase text-muted-foreground">
              {key}
            </dt>
            <dd class="mt-0.5 break-words text-sm text-foreground">
              {value || 'Not set'}
            </dd>
          </div>
        {/each}
      </dl>
    </div>
  {/if}
</section>
