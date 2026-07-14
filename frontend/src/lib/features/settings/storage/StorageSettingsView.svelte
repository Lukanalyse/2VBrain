<script lang="ts" context="module">
  import type { Component } from 'svelte';
</script>

<script lang="ts">
  import {
    AlertCircle,
    CheckCircle2,
    Database,
    ExternalLink,
    FolderOpen,
    FolderSearch,
    HardDrive,
    Loader2,
    SearchCode
  } from '@lucide/svelte';
  import { onMount } from 'svelte';

  import Card from '$lib/components/ui/Card.svelte';
  import SectionHeader from '$lib/components/ui/SectionHeader.svelte';
  import SettingsTabs from '$lib/features/settings/components/SettingsTabs.svelte';
  import {
    saveVaultPath,
    validateVault,
    waitForStorageStatus
  } from '$lib/services/storage';
  import {
    hasDesktopIntegration,
    openPath,
    revealPath,
    selectVaultFolder
  } from '$lib/services/desktop';
  import type { StorageStatus, VaultValidation } from '$lib/types/storage';

  let storageStatus: StorageStatus | null = null;
  let vaultPath = '';
  let validation: VaultValidation | null = null;
  let actionMessage: string | null = null;
  let isLoading = true;
  let isChecking = false;
  let isSaving = false;
  let desktopAvailable = false;

  $: canSave = Boolean(validation?.is_valid) && !isSaving;

  onMount(async () => {
    desktopAvailable = hasDesktopIntegration();
    try {
      storageStatus = await waitForStorageStatus();
      vaultPath = storageStatus.vault_path ?? '';
      if (vaultPath) {
        await validateCurrentVault();
      }
    } catch (error) {
      actionMessage =
        error instanceof Error
          ? error.message
          : 'Research OS local service is unavailable.';
    } finally {
      isLoading = false;
    }
  });

  async function browseForVault(): Promise<void> {
    actionMessage = null;
    if (!desktopAvailable) {
      actionMessage =
        'Browse is available in the desktop app. In Docker/browser mode, mount the host folder and paste the mounted path.';
      return;
    }

    const selectedPath = await selectVaultFolder();
    if (!selectedPath) return;

    vaultPath = selectedPath;
    await validateCurrentVault();
    if (validation?.is_valid) {
      await saveCurrentVault();
    }
  }

  async function validateCurrentVault(): Promise<void> {
    if (!vaultPath.trim()) {
      validation = {
        is_valid: false,
        vault_path: '',
        message: 'Vault path is required.',
        error_code: 'path_required',
        received_path: vaultPath,
        normalized_path: null,
        validated_by: 'frontend',
        failed_check: 'path_required',
        system_error: null,
        is_docker_path_issue: false
      };
      return;
    }

    isChecking = true;
    actionMessage = null;
    try {
      validation = await validateVault(vaultPath);
    } catch (error) {
      validation = {
        is_valid: false,
        vault_path: vaultPath,
        message:
          error instanceof Error
            ? error.message
            : 'Unable to validate the vault.',
        error_code: 'request_failed',
        received_path: vaultPath,
        normalized_path: null,
        validated_by: 'frontend',
        failed_check: 'api_request',
        system_error: error instanceof Error ? error.message : String(error),
        is_docker_path_issue: false
      };
    } finally {
      isChecking = false;
    }
  }

  async function saveCurrentVault(): Promise<void> {
    await validateCurrentVault();
    if (!validation?.is_valid) return;

    isSaving = true;
    try {
      storageStatus = await saveVaultPath(vaultPath);
      validation = {
        is_valid: storageStatus.is_configured,
        vault_path: storageStatus.vault_path ?? vaultPath,
        message:
          storageStatus.validation_message ?? 'Vault configuration saved.',
        error_code: storageStatus.is_configured ? null : 'save_failed',
        received_path: vaultPath,
        normalized_path: storageStatus.vault_path,
        validated_by: 'backend',
        failed_check: null,
        system_error: null,
        is_docker_path_issue: false
      };
    } finally {
      isSaving = false;
    }
  }

  async function handleOpen(path: string | null): Promise<void> {
    if (!path) {
      actionMessage = 'Open Folder is unavailable until a path is configured.';
      return;
    }
    actionMessage = (await openPath(path)) ?? `Opened ${path}.`;
  }

  async function handleReveal(path: string | null): Promise<void> {
    if (!path) {
      actionMessage =
        'Open in Finder / Explorer is unavailable until a path is configured.';
      return;
    }
    actionMessage = (await revealPath(path)) ?? `Revealed ${path}.`;
  }
</script>

<section class="px-4 py-6 lg:px-8 lg:py-8">
  <div class="mx-auto w-full max-w-5xl space-y-6">
    <SettingsTabs />
    <SectionHeader
      eyebrow="Settings"
      title="Storage"
      description="Manage local workspace paths while keeping Obsidian as the source of truth."
    />

    <Card className="p-5">
      <div class="flex items-start gap-4">
        <div
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-border bg-muted/60 text-accent"
        >
          <FolderOpen size={18} strokeWidth={1.8} />
        </div>
        <div class="min-w-0 flex-1">
          <div
            class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between"
          >
            <div>
              <h2 class="text-base font-semibold text-foreground">
                Obsidian Vault
              </h2>
              <p class="mt-1 text-sm leading-6 text-muted-foreground">
                Select a folder that contains an `.obsidian` directory.
              </p>
            </div>
            <div
              class={validation?.is_valid
                ? 'inline-flex items-center gap-2 rounded-md border border-accent/30 bg-accent/10 px-2.5 py-1.5 text-xs text-accent'
                : 'inline-flex items-center gap-2 rounded-md border border-border bg-muted/25 px-2.5 py-1.5 text-xs text-muted-foreground'}
            >
              {#if validation?.is_valid}
                <CheckCircle2 size={14} />
                Valid vault
              {:else}
                <AlertCircle size={14} />
                Not connected
              {/if}
            </div>
          </div>

          <div class="mt-5 flex flex-col gap-3 sm:flex-row">
            <button
              class="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-border bg-muted/30 px-3 text-sm text-muted-foreground transition hover:text-foreground"
              type="button"
              disabled={isLoading || isChecking}
              on:click={browseForVault}
            >
              <FolderSearch size={16} />
              Browse...
            </button>
            <input
              bind:value={vaultPath}
              class="h-10 min-w-0 flex-1 rounded-md border border-border bg-background/50 px-3 text-sm text-foreground outline-none transition placeholder:text-muted-foreground focus:border-accent/50"
              disabled={isLoading}
              placeholder="/Users/name/Documents/Obsidian Vault"
              on:blur={validateCurrentVault}
            />
            <button
              class="inline-flex h-10 items-center justify-center rounded-md border border-border bg-muted/30 px-3 text-sm text-muted-foreground transition hover:text-foreground disabled:opacity-60"
              type="button"
              disabled={isChecking}
              on:click={validateCurrentVault}
            >
              {#if isChecking}
                <Loader2 class="animate-spin" size={16} />
              {:else}
                Validate
              {/if}
            </button>
            <button
              class="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-accent px-3 text-sm font-medium text-accent-foreground transition hover:bg-accent/90 disabled:opacity-60"
              type="button"
              disabled={!canSave}
              on:click={saveCurrentVault}
            >
              {#if isSaving}
                <Loader2 class="animate-spin" size={16} />
              {:else}
                <CheckCircle2 size={16} />
              {/if}
              Save
            </button>
          </div>

          <div class="mt-3 flex flex-wrap gap-2">
            <button
              class="inline-flex h-8 items-center gap-2 rounded-md border border-border bg-background/40 px-2.5 text-xs text-muted-foreground transition hover:text-foreground"
              type="button"
              on:click={() => handleReveal(validation?.vault_path ?? vaultPath)}
            >
              <ExternalLink size={14} />
              Open in Finder / Explorer
            </button>
          </div>

          {#if validation}
            <div
              class={validation.is_valid
                ? 'mt-4 rounded-md border border-accent/30 bg-accent/10 px-3 py-3 text-sm text-accent'
                : 'mt-4 rounded-md border border-border bg-muted/25 px-3 py-3 text-sm text-muted-foreground'}
            >
              <p>{validation.message}</p>
              {#if validation.error_code}
                <p class="mt-2 text-xs">
                  Diagnostic: {validation.validated_by} failed `{validation.failed_check}`
                  for `{validation.normalized_path ??
                    validation.received_path}`.
                </p>
              {/if}
              {#if validation.system_error}
                <p class="mt-1 text-xs">System: {validation.system_error}</p>
              {/if}
            </div>
          {/if}

          {#if !desktopAvailable}
            <p class="mt-3 text-xs leading-5 text-muted-foreground">
              Native Browse and Finder / Explorer actions require the desktop
              shell. The Docker browser build validates mounted paths through
              the backend.
            </p>
          {/if}
        </div>
      </div>
    </Card>

    <div class="grid gap-4 lg:grid-cols-2">
      <Card className="p-5">
        {@render StorageRow({
          icon: FolderOpen,
          label: 'Vault',
          value: storageStatus?.vault_path ?? 'Not configured',
          onOpen: () => handleOpen(storageStatus?.vault_path ?? null),
          onReveal: () => handleReveal(storageStatus?.vault_path ?? null)
        })}
      </Card>

      <Card className="p-5">
        {@render StorageRow({
          icon: HardDrive,
          label: 'Research Library',
          value: storageStatus?.library_path ?? '../library',
          onOpen: () => handleOpen(storageStatus?.library_path ?? null),
          onReveal: () => handleReveal(storageStatus?.library_path ?? null)
        })}
      </Card>

      <Card className="p-5">
        {@render StorageRow({
          icon: Database,
          label: 'Database',
          value: storageStatus?.database_url ?? 'sqlite:///./research_os.db',
          onOpen: () => handleOpen(storageStatus?.database_url ?? null),
          onReveal: () => handleReveal(storageStatus?.database_url ?? null)
        })}
      </Card>

      <Card className="p-5">
        {@render StorageRow({
          icon: SearchCode,
          label: 'Vector Index',
          value:
            storageStatus?.vector_store_path ??
            storageStatus?.vector_store_provider ??
            'Not configured',
          onOpen: () => handleOpen(storageStatus?.vector_store_path ?? null),
          onReveal: () => handleReveal(storageStatus?.vector_store_path ?? null)
        })}
      </Card>
    </div>

    {#if actionMessage}
      <div
        class="rounded-md border border-border bg-muted/25 px-3 py-3 text-sm text-muted-foreground"
      >
        {actionMessage}
      </div>
    {/if}
  </div>
</section>

{#snippet StorageRow({
  icon,
  label,
  value,
  onOpen,
  onReveal
}: {
  icon: Component;
  label: string;
  value: string;
  onOpen: () => void;
  onReveal: () => void;
})}
  <div class="flex items-start gap-4">
    <div
      class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-border bg-background/50 text-accent"
    >
      <svelte:component this={icon} size={18} strokeWidth={1.8} />
    </div>
    <div class="min-w-0 flex-1">
      <p class="text-sm font-medium text-foreground">{label}</p>
      <p class="mt-1 truncate text-sm text-muted-foreground">{value}</p>
      <div class="mt-4 flex flex-wrap gap-2">
        <button
          class="h-8 rounded-md border border-border bg-background/40 px-2.5 text-xs text-muted-foreground transition hover:text-foreground"
          type="button"
          on:click={onOpen}
        >
          Open Folder
        </button>
        <button
          class="h-8 rounded-md border border-border bg-background/40 px-2.5 text-xs text-muted-foreground transition hover:text-foreground"
          type="button"
          on:click={onReveal}
        >
          Open in Finder / Explorer
        </button>
      </div>
    </div>
  </div>
{/snippet}
