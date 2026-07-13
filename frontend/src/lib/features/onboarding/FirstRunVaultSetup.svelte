<script lang="ts">
  import {
    AlertCircle,
    CheckCircle2,
    ExternalLink,
    FolderSearch,
    Loader2,
    ShieldCheck
  } from '@lucide/svelte';
  import { createEventDispatcher } from 'svelte';

  import Card from '$lib/components/ui/Card.svelte';
  import {
    hasDesktopIntegration,
    revealPath,
    selectVaultFolder
  } from '$lib/services/desktop';
  import { saveVaultPath, validateVault } from '$lib/services/storage';
  import type { StorageStatus, VaultValidation } from '$lib/types/storage';

  const dispatch = createEventDispatcher<{ configured: StorageStatus }>();

  let vaultPath = '';
  let validation: VaultValidation | null = null;
  let errorMessage: string | null = null;
  let actionMessage: string | null = null;
  let isChecking = false;
  let isSaving = false;
  let desktopAvailable = false;

  desktopAvailable = hasDesktopIntegration();

  async function browseForVault(): Promise<void> {
    errorMessage = null;
    actionMessage = null;
    if (!desktopAvailable) {
      actionMessage =
        'Browse is available in the desktop app. In Docker/browser mode, mount the host folder and paste the mounted path.';
      return;
    }

    const selectedPath = await selectVaultFolder();
    if (!selectedPath) return;

    vaultPath = selectedPath;
    const isValid = await checkVault();
    if (isValid) {
      await saveVault();
    }
  }

  async function checkVault(): Promise<boolean> {
    errorMessage = null;
    validation = null;
    isChecking = true;

    try {
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
        return false;
      }

      validation = await validateVault(vaultPath);
      return validation.is_valid;
    } catch {
      errorMessage =
        'Unable to validate the vault. Check that the backend is running.';
      return false;
    } finally {
      isChecking = false;
    }
  }

  async function saveVault(): Promise<void> {
    const isValid = await checkVault();
    if (!isValid) return;

    isSaving = true;
    try {
      const status = await saveVaultPath(vaultPath);
      dispatch('configured', status);
    } catch {
      errorMessage = 'Unable to save the workspace configuration.';
    } finally {
      isSaving = false;
    }
  }

  async function openSelectedFolder(): Promise<void> {
    if (!vaultPath.trim()) {
      actionMessage = 'Open in Finder / Explorer is unavailable until a path is selected.';
      return;
    }
    actionMessage = (await revealPath(vaultPath)) ?? `Revealed ${vaultPath}.`;
  }
</script>

<div
  class="fixed inset-0 z-50 flex items-center justify-center bg-background/95 px-4 backdrop-blur-xl"
>
  <Card className="w-full max-w-2xl p-6 sm:p-8">
    <div class="flex items-start gap-4">
      <div
        class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-border bg-muted/60 text-accent"
      >
        <ShieldCheck size={20} strokeWidth={1.8} />
      </div>
      <div class="min-w-0">
        <p class="text-xs font-medium uppercase text-accent">First Launch</p>
        <h1 class="mt-2 text-2xl font-semibold text-foreground">
          Connect an Obsidian Vault
        </h1>
        <p class="mt-3 text-sm leading-6 text-muted-foreground">
          Research OS reads from an existing Obsidian vault and stores only
          workspace metadata outside the vault.
        </p>
      </div>
    </div>

    <div class="mt-7 space-y-3">
      <label class="text-sm font-medium text-foreground" for="vault-path"
        >Vault folder</label
      >
      <div class="flex flex-col gap-3 sm:flex-row">
        <button
          class="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-border bg-muted/35 px-3 text-sm text-muted-foreground transition hover:text-foreground"
          type="button"
          disabled={isChecking || isSaving}
          on:click={browseForVault}
        >
          <FolderSearch size={16} />
          Browse...
        </button>
        <input
          id="vault-path"
          bind:value={vaultPath}
          class="h-10 min-w-0 flex-1 rounded-md border border-border bg-background/50 px-3 text-sm text-foreground outline-none transition placeholder:text-muted-foreground focus:border-accent/50"
          placeholder="/Users/name/Documents/Obsidian Vault"
          on:blur={checkVault}
        />
        <button
          class="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-border bg-muted/35 px-3 text-sm text-muted-foreground transition hover:text-foreground"
          type="button"
          on:click={openSelectedFolder}
        >
          <ExternalLink size={16} />
          Open
        </button>
      </div>
      <p class="text-xs leading-5 text-muted-foreground">
        A valid Vault must be a folder containing an `.obsidian` directory.
      </p>
    </div>

    {#if validation || errorMessage}
      <div
        class="mt-5 rounded-md border border-border bg-background/45 px-3 py-3"
      >
        <div class="flex items-start gap-2">
          {#if validation?.is_valid}
            <CheckCircle2 class="mt-0.5 text-accent" size={16} />
          {:else}
            <AlertCircle class="mt-0.5 text-muted-foreground" size={16} />
          {/if}
          <div class="min-w-0">
            <p
              class={validation?.is_valid
                ? 'text-sm text-accent'
                : 'text-sm text-muted-foreground'}
            >
              {errorMessage ?? validation?.message}
            </p>
            {#if validation?.error_code}
              <p class="mt-2 text-xs text-muted-foreground">
                Diagnostic: {validation.validated_by} failed `{validation.failed_check}` for `{validation.normalized_path ?? validation.received_path}`.
              </p>
            {/if}
          </div>
        </div>
      </div>
    {/if}

    {#if actionMessage}
      <div
        class="mt-5 rounded-md border border-border bg-muted/25 px-3 py-3 text-sm text-muted-foreground"
      >
        {actionMessage}
      </div>
    {/if}

    <div class="mt-7 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
      <button
        class="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-border bg-muted/30 px-4 text-sm text-muted-foreground transition hover:text-foreground disabled:cursor-not-allowed disabled:opacity-60"
        type="button"
        disabled={isChecking || isSaving}
        on:click={checkVault}
      >
        {#if isChecking}
          <Loader2 class="animate-spin" size={16} />
        {/if}
        Validate
      </button>
      <button
        class="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-accent px-4 text-sm font-medium text-accent-foreground transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-60"
        type="button"
        disabled={isChecking || isSaving}
        on:click={saveVault}
      >
        {#if isSaving}
          <Loader2 class="animate-spin" size={16} />
        {:else}
          <CheckCircle2 size={16} />
        {/if}
        Save Vault
      </button>
    </div>
  </Card>
</div>
