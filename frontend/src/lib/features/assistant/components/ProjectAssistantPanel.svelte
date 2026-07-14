<script lang="ts">
  import {
    ArrowUpRight,
    BrainCircuit,
    Check,
    Database,
    LoaderCircle,
    RefreshCw,
    Save,
    Send
  } from '@lucide/svelte';

  import {
    getAssistantStatus,
    getProjectIndex,
    indexProject,
    queryProject
  } from '$lib/features/assistant/services/assistantApi';
  import type {
    AssistantCitation,
    AssistantHistoryMessage,
    AssistantStatus,
    ProjectIndexStatus
  } from '$lib/features/assistant/types/assistant';
  import type { LinkableObject } from '$lib/features/linking/types/linking';
  import {
    createWorkspaceNote,
    saveWorkspaceNote
  } from '$lib/features/workspace/services/workspaceApi';

  type Props = {
    project: LinkableObject;
    openObject: (object: LinkableObject) => Promise<void>;
    refreshProject: () => Promise<void>;
  };

  type ChatMessage = {
    id: number;
    role: 'user' | 'assistant';
    content: string;
    question?: string;
    citations: AssistantCitation[];
    saved?: boolean;
  };

  const suggestions = [
    'Quelles sont les hypothèses encore ouvertes ?',
    'Quels résultats se contredisent dans ce projet ?',
    'Quelles informations importantes manquent encore ?'
  ];

  let { project, openObject, refreshProject }: Props = $props();
  let status = $state<AssistantStatus | null>(null);
  let indexStatus = $state<ProjectIndexStatus | null>(null);
  let messages = $state<ChatMessage[]>([]);
  let question = $state('');
  let loading = $state(true);
  let indexing = $state(false);
  let answering = $state(false);
  let savingMessageId = $state<number | null>(null);
  let error = $state<string | null>(null);
  let messageId = 0;

  let ready = $derived(Boolean(status?.available && indexStatus?.ready));

  $effect(() => {
    const projectId = project.id;
    messages = [];
    question = '';
    error = null;
    void load(projectId);
  });

  async function load(projectId = project.id): Promise<void> {
    loading = true;
    error = null;
    try {
      const [nextStatus, nextIndex] = await Promise.all([
        getAssistantStatus(),
        getProjectIndex(projectId)
      ]);
      if (project.id !== projectId) return;
      status = nextStatus;
      indexStatus = nextIndex;
    } catch (loadError) {
      if (project.id !== projectId) return;
      error =
        loadError instanceof Error
          ? loadError.message
          : 'Unable to load the assistant.';
    } finally {
      if (project.id === projectId) loading = false;
    }
  }

  async function prepareProject(): Promise<void> {
    if (indexing || !status?.available) return;
    indexing = true;
    error = null;
    try {
      indexStatus = await indexProject(project.id);
    } catch (indexError) {
      error =
        indexError instanceof Error
          ? indexError.message
          : 'Unable to index this project.';
    } finally {
      indexing = false;
    }
  }

  async function ask(value = question): Promise<void> {
    const prompt = value.trim();
    if (!prompt || answering || !ready) return;
    const history: AssistantHistoryMessage[] = messages
      .slice(-8)
      .map((message) => ({
        role: message.role,
        content: message.content
      }));
    messages = [
      ...messages,
      { id: ++messageId, role: 'user', content: prompt, citations: [] }
    ];
    question = '';
    answering = true;
    error = null;
    try {
      const response = await queryProject(project.id, prompt, history);
      messages = [
        ...messages,
        {
          id: ++messageId,
          role: 'assistant',
          content: response.answer,
          question: prompt,
          citations: response.citations
        }
      ];
      indexStatus = await getProjectIndex(project.id);
    } catch (queryError) {
      error =
        queryError instanceof Error
          ? queryError.message
          : 'Unable to answer this question.';
    } finally {
      answering = false;
    }
  }

  async function saveAnswer(message: ChatMessage): Promise<void> {
    if (
      message.role !== 'assistant' ||
      message.saved ||
      savingMessageId !== null
    )
      return;
    savingMessageId = message.id;
    error = null;
    try {
      const noteTitle = `Assistant - ${(message.question ?? 'Research answer').slice(0, 52)}`;
      const created = await createWorkspaceNote(project.id, noteTitle);
      const sources = message.citations.length
        ? `\n\n## Sources\n\n${message.citations
            .map(
              (citation) =>
                `- ${citation.label}: ${citation.source_title}${
                  citation.page_number ? `, page ${citation.page_number}` : ''
                }`
            )
            .join('\n')}`
        : '';
      const content = `${created.content.trim()}\n\n## Question\n\n${
        message.question ?? ''
      }\n\n## Assistant answer\n\n${message.content}${sources}\n`;
      await saveWorkspaceNote(project.id, created.note.id, content);
      messages = messages.map((entry) =>
        entry.id === message.id ? { ...entry, saved: true } : entry
      );
      await refreshProject();
    } catch (saveError) {
      error =
        saveError instanceof Error
          ? saveError.message
          : 'Unable to save this answer.';
    } finally {
      savingMessageId = null;
    }
  }

  function handleComposerKey(event: KeyboardEvent): void {
    if (event.key !== 'Enter' || event.shiftKey) return;
    event.preventDefault();
    void ask();
  }
</script>

<section
  class="border-b border-border bg-surface/45"
  aria-label="Project research assistant"
>
  <header
    class="flex flex-wrap items-center justify-between gap-3 border-b border-border/80 px-6 py-3"
  >
    <div class="flex min-w-0 items-center gap-3">
      <span
        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-accent/35 bg-accent/10 text-accent"
      >
        <BrainCircuit size={16} />
      </span>
      <div class="min-w-0">
        <p class="text-sm font-semibold text-foreground">Research Assistant</p>
        <p class="truncate text-xs text-muted-foreground">
          {status?.config.chat_model ?? 'Ollama'} · {project.title}
        </p>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <span
        class="inline-flex h-7 items-center gap-1.5 rounded-md border border-accent/30 bg-accent/[0.07] px-2 text-[0.68rem] font-medium text-accent"
      >
        <Check size={12} /> Project only
      </span>
      <button
        type="button"
        class="flex h-8 w-8 items-center justify-center rounded-md border border-border text-muted-foreground transition hover:text-foreground"
        aria-label="Refresh assistant status"
        title="Refresh status"
        disabled={loading || indexing || answering}
        onclick={() => load()}
      >
        <RefreshCw size={14} class={loading ? 'animate-spin' : undefined} />
      </button>
    </div>
  </header>

  <div
    class="grid min-h-[390px] grid-cols-[minmax(0,1fr)] lg:grid-cols-[minmax(0,1.4fr)_minmax(250px,0.6fr)]"
  >
    <div
      class="flex min-h-0 flex-col border-b border-border/80 lg:border-b-0 lg:border-r"
    >
      <div
        class="max-h-[390px] min-h-64 flex-1 overflow-y-auto px-6 py-4"
        aria-live="polite"
      >
        {#if loading}
          <div
            class="flex min-h-52 items-center justify-center text-muted-foreground"
          >
            <LoaderCircle size={18} class="animate-spin" />
          </div>
        {:else if !status?.available}
          <div
            class="flex min-h-52 flex-col items-center justify-center text-center"
          >
            <BrainCircuit size={24} class="text-muted-foreground" />
            <p class="mt-3 text-sm font-medium text-foreground">
              Ollama is unavailable
            </p>
            <a
              class="mt-3 text-xs text-accent hover:underline"
              href="/settings/ai"
            >
              Open Local AI settings
            </a>
          </div>
        {:else if !indexStatus?.ready}
          <div
            class="flex min-h-52 flex-col items-center justify-center text-center"
          >
            <Database size={23} class="text-muted-foreground" />
            <p class="mt-3 text-sm font-medium text-foreground">
              Project index not ready
            </p>
            <button
              type="button"
              class="mt-4 inline-flex h-9 items-center gap-2 rounded-md bg-accent px-3 text-xs font-semibold text-accent-foreground disabled:opacity-50"
              disabled={indexing}
              onclick={prepareProject}
            >
              {#if indexing}
                <LoaderCircle size={14} class="animate-spin" /> Indexing
              {:else}
                <Database size={14} /> Prepare project
              {/if}
            </button>
          </div>
        {:else if messages.length === 0}
          <div class="grid min-h-52 content-center gap-2">
            {#each suggestions as suggestion}
              <button
                type="button"
                class="w-full border border-border bg-background/50 px-3 py-2.5 text-left text-sm text-muted-foreground transition hover:border-accent/35 hover:text-foreground"
                onclick={() => ask(suggestion)}
              >
                {suggestion}
              </button>
            {/each}
          </div>
        {:else}
          <div class="space-y-4">
            {#each messages as message (message.id)}
              <article
                class={message.role === 'user'
                  ? 'ml-auto max-w-[82%]'
                  : 'max-w-[94%]'}
              >
                <p class="text-[0.65rem] uppercase text-muted-foreground">
                  {message.role === 'user' ? 'You' : 'Assistant'}
                </p>
                <p
                  class={message.role === 'user'
                    ? 'mt-1 whitespace-pre-wrap rounded-md bg-muted/55 px-3 py-2 text-sm leading-6 text-foreground'
                    : 'mt-1 whitespace-pre-wrap text-sm leading-6 text-foreground'}
                >
                  {message.content}
                </p>
                {#if message.role === 'assistant'}
                  <div class="mt-2 flex flex-wrap items-center gap-1.5">
                    {#each message.citations as citation}
                      <button
                        type="button"
                        class="inline-flex h-7 max-w-56 items-center gap-1.5 rounded-md border border-border bg-background/55 px-2 text-[0.68rem] text-muted-foreground transition hover:border-accent/40 hover:text-foreground"
                        title={citation.excerpt}
                        onclick={() => openObject(citation.object)}
                      >
                        <span class="font-semibold text-accent"
                          >{citation.label}</span
                        >
                        <span class="truncate">{citation.source_title}</span>
                        {#if citation.page_number}<span
                            >p.{citation.page_number}</span
                          >{/if}
                        <ArrowUpRight size={11} />
                      </button>
                    {/each}
                    {#if !message.saved}
                      <button
                        type="button"
                        class="flex h-7 w-7 items-center justify-center rounded-md border border-border text-muted-foreground transition hover:text-foreground"
                        aria-label="Save answer as project note"
                        title="Save as project note"
                        disabled={savingMessageId !== null}
                        onclick={() => saveAnswer(message)}
                      >
                        {#if savingMessageId === message.id}
                          <LoaderCircle size={12} class="animate-spin" />
                        {:else}
                          <Save size={12} />
                        {/if}
                      </button>
                    {:else}
                      <span
                        class="inline-flex h-7 items-center gap-1 text-[0.68rem] text-accent"
                      >
                        <Check size={12} /> Saved
                      </span>
                    {/if}
                  </div>
                {/if}
              </article>
            {/each}
            {#if answering}
              <div
                class="flex items-center gap-2 text-xs text-muted-foreground"
              >
                <LoaderCircle size={13} class="animate-spin" /> Reading project sources
              </div>
            {/if}
          </div>
        {/if}
      </div>

      <div class="border-t border-border/80 p-3">
        <div class="flex min-w-0 items-end gap-2">
          <textarea
            bind:value={question}
            class="min-h-10 max-h-28 min-w-0 flex-1 resize-none rounded-md border border-border bg-background px-3 py-2 text-sm leading-5 text-foreground outline-none placeholder:text-muted-foreground focus:border-accent/50 disabled:opacity-50"
            rows="1"
            placeholder="Ask this project..."
            disabled={!ready || answering}
            onkeydown={handleComposerKey}
          ></textarea>
          <button
            type="button"
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-accent text-accent-foreground disabled:opacity-40"
            aria-label="Send question"
            title="Send"
            disabled={!ready || answering || !question.trim()}
            onclick={() => ask()}
          >
            {#if answering}<LoaderCircle
                size={15}
                class="animate-spin"
              />{:else}<Send size={15} />{/if}
          </button>
        </div>
      </div>
    </div>

    <aside class="max-h-[470px] overflow-y-auto px-4 py-4">
      <p class="text-[0.68rem] font-medium uppercase text-muted-foreground">
        Local index
      </p>
      <dl class="mt-3 grid grid-cols-2 gap-2">
        <div class="border border-border bg-background/40 px-3 py-2">
          <dt class="text-[0.65rem] text-muted-foreground">Documents</dt>
          <dd class="mt-1 text-lg font-semibold text-foreground">
            {indexStatus?.document_count ?? 0}
          </dd>
        </div>
        <div class="border border-border bg-background/40 px-3 py-2">
          <dt class="text-[0.65rem] text-muted-foreground">Passages</dt>
          <dd class="mt-1 text-lg font-semibold text-foreground">
            {indexStatus?.chunk_count ?? 0}
          </dd>
        </div>
      </dl>
      <div class="mt-4 border-t border-border/80 pt-3">
        <p class="text-[0.65rem] uppercase text-muted-foreground">Embedding</p>
        <p class="mt-1 truncate text-xs text-foreground">
          {indexStatus?.embedding_model ??
            status?.config.embedding_model ??
            'Not configured'}
        </p>
      </div>
      {#if indexStatus?.errors.length}
        <div class="mt-4 border-l-2 border-entity-review pl-3">
          {#each indexStatus.errors.slice(0, 3) as indexError}
            <p class="text-xs leading-5 text-muted-foreground">{indexError}</p>
          {/each}
        </div>
      {/if}
      {#if error}
        <p class="mt-4 text-xs leading-5 text-entity-review">{error}</p>
      {/if}
    </aside>
  </div>
</section>
