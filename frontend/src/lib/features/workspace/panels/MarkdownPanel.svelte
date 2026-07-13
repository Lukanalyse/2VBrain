<script lang="ts">
  import type { LinkableObject } from '$lib/features/linking/types/linking';
  import type { WorkspacePanelContext } from '$lib/features/workspace/types/panels';

  type Props = {
    context: WorkspacePanelContext;
    compact?: boolean;
  };

  let { context, compact = false }: Props = $props();
  let textarea: HTMLTextAreaElement;
  let suggestions = $state<LinkableObject[]>([]);
  let activeSuggestion = $state(0);
  let completionStart = -1;
  let completionQuery = '';

  async function handleInput(event: Event): Promise<void> {
    const value = (event.currentTarget as HTMLTextAreaElement).value;
    context.updateContent(value);
    await updateCompletions(value, textarea.selectionStart);
  }

  async function updateCompletions(
    value: string,
    cursor: number
  ): Promise<void> {
    const beforeCursor = value.slice(0, cursor);
    const match = beforeCursor.match(/\[\[([^\]\n]*)$/);
    if (!match) {
      closeCompletions();
      return;
    }

    completionQuery = match[1];
    completionStart = cursor - match[0].length;
    suggestions = (await context.searchObjects(completionQuery)).slice(0, 8);
    activeSuggestion = 0;
  }

  function closeCompletions(): void {
    suggestions = [];
    activeSuggestion = 0;
    completionStart = -1;
    completionQuery = '';
  }

  function applySuggestion(item: LinkableObject): void {
    if (completionStart < 0) return;
    const cursor = textarea.selectionStart;
    const before = context.content.slice(0, completionStart);
    const after = context.content.slice(cursor);
    const replacement = `[[${item.title}]]`;
    const next = `${before}${replacement}${after}`;
    context.updateContent(next);
    closeCompletions();
    requestAnimationFrame(() => {
      textarea.focus();
      const nextCursor = before.length + replacement.length;
      textarea.setSelectionRange(nextCursor, nextCursor);
    });
  }

  function handleKeydown(event: KeyboardEvent): void {
    if (!suggestions.length) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      activeSuggestion = (activeSuggestion + 1) % suggestions.length;
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      activeSuggestion =
        (activeSuggestion - 1 + suggestions.length) % suggestions.length;
    } else if (event.key === 'Enter' || event.key === 'Tab') {
      event.preventDefault();
      applySuggestion(suggestions[activeSuggestion]);
    } else if (event.key === 'Escape') {
      closeCompletions();
    }
  }
</script>

<div class="relative flex h-full min-h-0 flex-col bg-background">
  <textarea
    bind:this={textarea}
    class={[
      'w-full resize-none border-0 bg-background font-mono text-[0.94rem] leading-7 text-foreground caret-accent outline-none selection:bg-accent/20',
      compact
        ? 'min-h-[620px] p-6 pb-28'
        : 'min-h-0 flex-1 overflow-auto px-8 py-7 pb-32'
    ]}
    style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace; text-rendering: geometricPrecision; -webkit-font-smoothing: antialiased;"
    spellcheck="true"
    value={context.content}
    oninput={handleInput}
    onkeydown={handleKeydown}
    onblur={() => setTimeout(closeCompletions, 120)}
  ></textarea>

  {#if suggestions.length}
    <div
      class="absolute left-6 top-14 z-20 w-80 overflow-hidden rounded-lg border border-border bg-background shadow-2xl shadow-black/40"
    >
      <div
        class="border-b border-border px-3 py-2 text-xs font-medium uppercase text-muted-foreground"
      >
        Link object
      </div>
      <div class="max-h-72 overflow-auto p-1">
        {#each suggestions as item, index}
          <button
            class={index === activeSuggestion
              ? 'flex w-full items-center justify-between gap-3 rounded-md bg-muted px-2 py-2 text-left text-sm text-foreground'
              : 'flex w-full items-center justify-between gap-3 rounded-md px-2 py-2 text-left text-sm text-muted-foreground hover:bg-muted/60 hover:text-foreground'}
            type="button"
            onmousedown={(event) => {
              event.preventDefault();
              applySuggestion(item);
            }}
          >
            <span class="min-w-0 truncate">{item.title}</span>
            <span class="text-xs capitalize text-muted-foreground"
              >{item.type}</span
            >
          </button>
        {/each}
      </div>
    </div>
  {/if}
</div>
