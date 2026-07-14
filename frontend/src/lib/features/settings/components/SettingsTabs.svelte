<script lang="ts">
  import { page } from '$app/stores';
  import { BrainCircuit, HardDrive } from '@lucide/svelte';

  const tabs = [
    { href: '/settings/storage', label: 'Storage', icon: HardDrive },
    { href: '/settings/ai', label: 'Local AI', icon: BrainCircuit }
  ];
</script>

<nav
  class="flex items-center gap-1 border-b border-border pb-3"
  aria-label="Settings sections"
>
  {#each tabs as tab}
    {@const Icon = tab.icon}
    <a
      href={tab.href}
      class={$page.url.pathname === tab.href
        ? 'inline-flex h-9 items-center gap-2 rounded-md bg-muted px-3 text-sm font-medium text-foreground'
        : 'inline-flex h-9 items-center gap-2 rounded-md px-3 text-sm text-muted-foreground transition hover:bg-muted/50 hover:text-foreground'}
      aria-current={$page.url.pathname === tab.href ? 'page' : undefined}
    >
      <Icon size={15} />
      {tab.label}
    </a>
  {/each}
</nav>
