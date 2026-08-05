<script lang="ts">
  import { page } from '$app/stores';
  import { Cpu, Settings } from '@lucide/svelte';
  import { onMount } from 'svelte';

  import FirstRunVaultSetup from '$lib/features/onboarding/FirstRunVaultSetup.svelte';
  import GlobalSearch from '$lib/features/search/GlobalSearch.svelte';
  import { navigationItems } from '$lib/layouts/navigation';
  import { waitForStorageStatus } from '$lib/services/storage';
  import type { StorageStatus } from '$lib/types/storage';
  import { cn } from '$lib/utils';

  let storageStatus: StorageStatus | null = null;
  let storageError: string | null = null;

  $: currentPath = $page.url.pathname;
  $: vaultLabel = storageStatus?.vault_path ?? 'Vault not configured';
  $: primaryItems = navigationItems.filter((item) => item.label !== 'Settings');

  onMount(async () => {
    try {
      storageStatus = await waitForStorageStatus();
      storageError = null;
    } catch {
      storageError = 'Local service unavailable. Restart Research OS to retry.';
    }
  });
</script>

<svelte:head>
  <title>Research OS</title>
</svelte:head>

<div
  class="flex h-screen flex-col overflow-hidden bg-background text-foreground"
>
  <header
    class="relative z-30 flex h-16 shrink-0 items-center border-b border-border/90 bg-surface/95 px-3 shadow-panel sm:px-5"
  >
    <a
      class="flex min-w-0 items-center gap-3"
      href="/"
      aria-label="Research OS Home"
    >
      <span class="core-mark" aria-hidden="true">
        <Cpu size={17} strokeWidth={1.8} />
      </span>
      <span class="hidden min-w-0 sm:block">
        <span class="block truncate text-sm font-semibold">Research OS</span>
        <span class="block truncate text-[11px] text-muted-foreground">
          Cognitive workspace
        </span>
      </span>
    </a>

    <nav
      class="absolute left-1/2 hidden h-10 -translate-x-1/2 items-center gap-1 rounded-lg border border-border/90 bg-surface-raised/65 p-1 md:flex"
      aria-label="Primary navigation"
    >
      {#each primaryItems as item}
        {@const Icon = item.icon}
        <a
          href={item.href}
          class={cn(
            'flex h-8 items-center gap-2 rounded-md px-3 text-xs font-medium transition-colors',
            currentPath === item.href
              ? 'bg-muted/80 text-foreground shadow-panel'
              : 'text-muted-foreground hover:bg-muted/65 hover:text-foreground'
          )}
          aria-current={currentPath === item.href ? 'page' : undefined}
        >
          <Icon size={15} strokeWidth={1.8} />
          <span>{item.label}</span>
        </a>
      {/each}
    </nav>

    <div class="ml-auto flex min-w-0 items-center gap-2">
      <div class="hidden w-[min(28vw,330px)] xl:block">
        <GlobalSearch compact />
      </div>
      <span
        class="hidden max-w-40 items-center gap-2 truncate px-2 text-[11px] text-muted-foreground lg:flex xl:hidden"
        title={vaultLabel}
      >
        <span
          class={storageStatus?.is_configured
            ? 'h-1.5 w-1.5 shrink-0 bg-accent'
            : 'h-1.5 w-1.5 shrink-0 bg-muted-foreground'}
        ></span>
        <span class="truncate">{vaultLabel}</span>
      </span>
      <a
        href="/settings/storage"
        class={cn(
          'inline-flex h-9 w-9 items-center justify-center rounded-md border border-border/90 bg-surface-raised/70 text-muted-foreground transition hover:border-accent/40 hover:bg-muted/65 hover:text-foreground',
          currentPath.startsWith('/settings') &&
            'border-accent/40 text-foreground'
        )}
        aria-label="Settings"
        title="Settings"
      >
        <Settings size={16} />
      </a>
    </div>

    <div
      class="pointer-events-none absolute inset-x-0 bottom-0 h-px core-signal"
    ></div>
  </header>

  <main class="min-h-0 flex-1 overflow-y-auto pb-16 md:pb-0">
    {#if storageError}
      <div
        class="border-b border-border bg-muted/25 px-4 py-2 text-xs text-muted-foreground"
      >
        {storageError}
      </div>
    {/if}
    <slot />
  </main>

  <nav
    class="fixed inset-x-0 bottom-0 z-40 grid h-16 grid-cols-5 border-t border-border/90 bg-surface/95 px-1 shadow-[0_-8px_24px_hsl(0_0%_0%/0.22)] backdrop-blur md:hidden"
    aria-label="Primary navigation"
  >
    {#each primaryItems as item}
      {@const Icon = item.icon}
      <a
        href={item.href}
        class={cn(
          'relative flex min-w-0 flex-col items-center justify-center gap-1 text-[10px] font-medium transition-colors',
          currentPath === item.href
            ? 'text-foreground'
            : 'text-muted-foreground'
        )}
        aria-current={currentPath === item.href ? 'page' : undefined}
      >
        {#if currentPath === item.href}
          <span class="absolute inset-x-5 top-0 h-0.5 bg-accent"></span>
        {/if}
        <Icon size={18} strokeWidth={currentPath === item.href ? 2 : 1.7} />
        <span class="truncate">{item.label}</span>
      </a>
    {/each}
  </nav>
</div>

{#if storageStatus && !storageStatus.is_configured}
  <FirstRunVaultSetup
    on:configured={(event) => (storageStatus = event.detail)}
  />
{/if}

<style>
  .core-mark {
    position: relative;
    display: inline-flex;
    width: 36px;
    height: 36px;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    border: 1px solid hsl(var(--accent) / 0.42);
    border-radius: 7px;
    color: hsl(var(--accent));
    background:
      linear-gradient(hsl(var(--foreground) / 0.075) 1px, transparent 1px),
      linear-gradient(
        90deg,
        hsl(var(--foreground) / 0.075) 1px,
        transparent 1px
      ),
      hsl(var(--surface-raised) / 0.88);
    background-size: 6px 6px;
    box-shadow: inset 0 0 0 3px hsl(var(--background) / 0.45);
  }

  .core-mark::before,
  .core-mark::after {
    content: '';
    position: absolute;
    top: 7px;
    bottom: 7px;
    width: 3px;
    border-block: 1px solid hsl(var(--muted-foreground) / 0.7);
  }

  .core-mark::before {
    left: -4px;
  }

  .core-mark::after {
    right: -4px;
  }

  .core-signal {
    background: linear-gradient(
      90deg,
      transparent 0%,
      hsl(var(--accent) / 0.12) 28%,
      hsl(var(--accent) / 0.6) 50%,
      hsl(var(--accent) / 0.12) 72%,
      transparent 100%
    );
  }
</style>
