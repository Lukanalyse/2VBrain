<script lang="ts">
  import 'katex/dist/katex.min.css';

  import { renderMarkdownPreview } from '$lib/features/research-workspace/markdownPreview';

  type Props = {
    content: string;
  };

  let { content }: Props = $props();
  let rendered = $derived(renderMarkdownPreview(content));
</script>

<div class="assistant-answer">
  {@html rendered.html}
</div>

<style>
  .assistant-answer {
    color: hsl(var(--foreground));
    font-size: 0.875rem;
    line-height: 1.5rem;
    min-width: 0;
    overflow-wrap: anywhere;
  }

  :global(.assistant-answer > *:first-child) {
    margin-top: 0;
  }

  :global(.assistant-answer > *:last-child) {
    margin-bottom: 0;
  }

  :global(.assistant-answer p) {
    margin: 0.55rem 0;
  }

  :global(.assistant-answer h1),
  :global(.assistant-answer h2),
  :global(.assistant-answer h3) {
    color: hsl(var(--foreground));
    font-size: 0.92rem;
    font-weight: 700;
    letter-spacing: 0;
    line-height: 1.4;
    margin: 1rem 0 0.4rem;
  }

  :global(.assistant-answer ul),
  :global(.assistant-answer ol) {
    margin: 0.55rem 0 0.7rem 1.15rem;
    padding: 0;
  }

  :global(.assistant-answer li) {
    margin: 0.25rem 0;
    padding-left: 0.15rem;
  }

  :global(.assistant-answer strong) {
    font-weight: 700;
  }

  :global(.assistant-answer code) {
    border: 1px solid hsl(var(--border));
    border-radius: 4px;
    background: hsl(var(--muted) / 0.55);
    font-family:
      ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.86em;
    padding: 0.08rem 0.28rem;
  }

  :global(.assistant-answer pre.code-block) {
    border: 1px solid hsl(var(--border));
    border-radius: 6px;
    background: hsl(240 7% 5%);
    margin: 0.75rem 0;
    max-width: 100%;
    overflow: auto;
    padding: 0.75rem;
  }

  :global(.assistant-answer pre.code-block code) {
    border: 0;
    background: transparent;
    display: block;
    padding: 0;
  }

  :global(.assistant-answer .math-inline) {
    color: hsl(var(--foreground));
    max-width: 100%;
  }

  :global(.assistant-answer .math-block) {
    margin: 0.8rem 0;
    max-width: 100%;
    overflow-x: auto;
    padding: 0.35rem 0;
  }

  :global(.assistant-answer .katex-display) {
    margin: 0;
    text-align: left;
  }

  :global(.assistant-answer .table-scroll) {
    margin: 0.75rem 0;
    max-width: 100%;
    overflow-x: auto;
  }

  :global(.assistant-answer table) {
    border-collapse: collapse;
    min-width: 100%;
  }

  :global(.assistant-answer th),
  :global(.assistant-answer td) {
    border: 1px solid hsl(var(--border));
    padding: 0.4rem 0.55rem;
    text-align: left;
    vertical-align: top;
  }
</style>
