<script lang="ts">
  import { Archive, BookOpen, Inbox, Library, Star } from '@lucide/svelte';

  import { cn } from '$lib/utils';

  const items = [
    { label: 'Library', icon: Library, active: true },
    { label: 'Inbox', icon: Inbox },
    { label: 'Collections', icon: BookOpen },
    { label: 'Reading', icon: BookOpen },
    { label: 'Favorites', icon: Star },
    { label: 'Archive', icon: Archive }
  ];
</script>

<aside
  class="border-b border-border bg-background/40 p-3 lg:w-56 lg:border-b-0 lg:border-r"
>
  <nav class="flex gap-1 overflow-x-auto lg:block lg:space-y-1">
    {#each items as item}
      <button
        class={cn(
          'flex h-9 shrink-0 items-center gap-2 rounded-md px-3 text-sm transition-colors lg:w-full',
          item.active
            ? 'border border-border bg-muted text-foreground'
            : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'
        )}
        type="button"
      >
        <svelte:component this={item.icon} size={15} strokeWidth={1.8} />
        {item.label}
      </button>
    {/each}
  </nav>
</aside>
