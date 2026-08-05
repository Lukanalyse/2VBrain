<script lang="ts">
  import {
    BrainCircuit,
    CheckCircle2,
    CircleAlert,
    LoaderCircle,
    RefreshCw,
    Save
  } from '@lucide/svelte';
  import { onMount } from 'svelte';

  import Card from '$lib/components/ui/Card.svelte';
  import SectionHeader from '$lib/components/ui/SectionHeader.svelte';
  import {
    getAssistantStatus,
    saveAssistantConfig
  } from '$lib/features/assistant/services/assistantApi';
  import type { AssistantStatus } from '$lib/features/assistant/types/assistant';
  import SettingsTabs from '$lib/features/settings/components/SettingsTabs.svelte';

  type ResearchModelChoice = {
    id: 'qwen3:14b' | 'qwen3.5:4b';
    label: string;
    recommendedContext: number;
  };

  const researchModels: ResearchModelChoice[] = [
    { id: 'qwen3:14b', label: 'Quality', recommendedContext: 16384 },
    { id: 'qwen3.5:4b', label: 'Efficient', recommendedContext: 8192 }
  ];

  let status = $state<AssistantStatus | null>(null);
  let chatModel = $state('qwen3:14b');
  let embeddingModel = $state('embeddinggemma');
  let contextLength = $state(16384);
  let loading = $state(true);
  let saving = $state(false);
  let message = $state<string | null>(null);
  let error = $state<string | null>(null);

  let chatModels = $derived(
    status?.models.filter(
      (model) => !model.name.toLowerCase().includes('embed')
    ) ?? []
  );
  let embeddingModels = $derived(
    status?.models.filter((model) =>
      model.name.toLowerCase().includes('embed')
    ) ?? []
  );
  let selectedChatModel = $derived(installedChatModel(chatModel));

  function modelMatches(installed: string, configured: string): boolean {
    return (
      installed === configured ||
      installed === `${configured}:latest` ||
      configured === `${installed}:latest`
    );
  }

  function installedChatModel(modelName: string) {
    return chatModels.find((model) => modelMatches(model.name, modelName));
  }

  function selectResearchModel(choice: ResearchModelChoice): void {
    if (!installedChatModel(choice.id)) return;
    chatModel = choice.id;
    contextLength = choice.recommendedContext;
  }

  function formatModelSize(size: number | null): string {
    if (!size) return '';
    return `${(size / 1_000_000_000).toFixed(1)} GB`;
  }

  onMount(() => void loadStatus());

  async function loadStatus(): Promise<void> {
    loading = true;
    error = null;
    try {
      status = await getAssistantStatus();
      chatModel = status.config.chat_model;
      embeddingModel = status.config.embedding_model;
      contextLength = status.config.context_length;
    } catch (loadError) {
      error =
        loadError instanceof Error
          ? loadError.message
          : 'Unable to load local AI status.';
    } finally {
      loading = false;
    }
  }

  async function save(): Promise<void> {
    if (saving || !chatModel.trim() || !embeddingModel.trim()) return;
    saving = true;
    message = null;
    error = null;
    try {
      await saveAssistantConfig({
        chat_model: chatModel.trim(),
        embedding_model: embeddingModel.trim(),
        context_length: contextLength
      });
      message = 'Local AI configuration saved.';
      await loadStatus();
    } catch (saveError) {
      error =
        saveError instanceof Error
          ? saveError.message
          : 'Unable to save local AI settings.';
    } finally {
      saving = false;
    }
  }
</script>

<section class="px-4 py-6 lg:px-8 lg:py-8">
  <div class="mx-auto w-full max-w-5xl space-y-6">
    <SettingsTabs />
    <SectionHeader
      eyebrow="Settings"
      title="Local AI"
      description="Configure the Ollama models used inside project-scoped research sessions."
    />

    <Card className="p-5">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div class="flex min-w-0 items-start gap-3">
          <span
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-border bg-muted/50 text-accent"
          >
            <BrainCircuit size={18} />
          </span>
          <div class="min-w-0">
            <h2 class="text-base font-semibold text-foreground">Ollama</h2>
            <p class="mt-1 truncate text-sm text-muted-foreground">
              {status?.config.base_url ?? 'http://127.0.0.1:11434'}
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span
            class={status?.available
              ? 'inline-flex h-8 items-center gap-2 rounded-md border border-accent/35 bg-accent/10 px-2.5 text-xs text-accent'
              : 'inline-flex h-8 items-center gap-2 rounded-md border border-border bg-muted/30 px-2.5 text-xs text-muted-foreground'}
          >
            {#if status?.available}
              <CheckCircle2 size={14} /> Local service ready
            {:else}
              <CircleAlert size={14} /> Local service unavailable
            {/if}
          </span>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-md border border-border text-muted-foreground transition hover:text-foreground"
            aria-label="Refresh Ollama status"
            title="Refresh status"
            disabled={loading}
            onclick={loadStatus}
          >
            <RefreshCw size={14} class={loading ? 'animate-spin' : undefined} />
          </button>
        </div>
      </div>

      {#if status?.error}
        <p
          class="mt-4 border-l-2 border-entity-review px-3 text-sm text-muted-foreground"
        >
          {status.error}
        </p>
      {/if}
    </Card>

    <div
      class="grid gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(280px,0.65fr)]"
    >
      <Card className="p-5">
        <p class="text-sm font-semibold text-foreground">Research model</p>
        <div
          class="mt-3 grid gap-2 sm:grid-cols-2"
          role="radiogroup"
          aria-label="Research model"
        >
          {#each researchModels as model}
            {@const installed = installedChatModel(model.id)}
            <button
              type="button"
              role="radio"
              aria-checked={chatModel === model.id}
              disabled={!installed}
              class={[
                'flex min-h-24 min-w-0 flex-col justify-between rounded-md border p-3 text-left transition disabled:cursor-not-allowed disabled:opacity-45',
                chatModel === model.id
                  ? 'border-accent/60 bg-accent/10 text-foreground'
                  : 'border-border bg-background/55 text-muted-foreground hover:border-accent/35 hover:text-foreground'
              ]}
              onclick={() => selectResearchModel(model)}
            >
              <span
                class="flex w-full min-w-0 items-start justify-between gap-2"
              >
                <span class="min-w-0">
                  <span
                    class="block text-xs font-semibold uppercase text-accent"
                  >
                    {model.label}
                  </span>
                  <span class="mt-1 block truncate text-sm font-medium">
                    {model.id}
                  </span>
                </span>
                {#if chatModel === model.id}
                  <CheckCircle2 size={16} class="shrink-0 text-accent" />
                {/if}
              </span>
              <span class="mt-3 text-xs text-muted-foreground">
                {#if installed}
                  {installed.parameter_size ?? 'Installed'}
                  {#if formatModelSize(installed.size)}
                    · {formatModelSize(installed.size)}
                  {/if}
                {:else}
                  Not installed
                {/if}
              </span>
            </button>
          {/each}
        </div>
      </Card>

      <Card className="p-5">
        <label
          class="text-sm font-semibold text-foreground"
          for="embedding-model"
        >
          Search model
        </label>
        <input
          id="embedding-model"
          list="embedding-models"
          bind:value={embeddingModel}
          class="mt-3 h-10 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground outline-none focus:border-accent/55"
        />
        <datalist id="embedding-models">
          {#each embeddingModels as model}
            <option value={model.name}
              >{model.parameter_size ?? model.name}</option
            >
          {/each}
        </datalist>
        <p class="mt-2 text-xs text-muted-foreground">
          {embeddingModels.find((model) =>
            modelMatches(model.name, embeddingModel)
          )?.parameter_size ?? 'Embedding model must be installed in Ollama.'}
        </p>
      </Card>
    </div>

    <Card className="p-5">
      <div class="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p class="text-sm font-semibold text-foreground">Context window</p>
          <div
            class="mt-3 flex items-center gap-1 rounded-md border border-border bg-muted/15 p-1"
            aria-label="Context window"
          >
            {#each [8192, 16384, 32768] as size}
              <button
                type="button"
                class={contextLength === size
                  ? 'h-8 rounded bg-background px-3 text-xs font-medium text-foreground shadow-sm'
                  : 'h-8 rounded px-3 text-xs text-muted-foreground hover:text-foreground'}
                onclick={() => (contextLength = size)}
              >
                {size / 1024}K
              </button>
            {/each}
          </div>
        </div>
        <button
          type="button"
          class="inline-flex h-10 items-center gap-2 rounded-md bg-accent px-3 text-sm font-medium text-accent-foreground disabled:opacity-50"
          disabled={saving || !selectedChatModel || !embeddingModel.trim()}
          onclick={save}
        >
          {#if saving}
            <LoaderCircle size={15} class="animate-spin" />
          {:else}
            <Save size={15} />
          {/if}
          Save
        </button>
      </div>
    </Card>

    {#if message}
      <p class="text-sm text-accent">{message}</p>
    {/if}
    {#if error}
      <p class="text-sm text-entity-review">{error}</p>
    {/if}
  </div>
</section>
