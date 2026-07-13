<script lang="ts">
  import 'katex/dist/katex.min.css';

  import { renderMarkdownPreview } from './markdownPreview';

  type Props = {
    content: string;
    objectTitle: string;
    compact?: boolean;
    showMetadata?: boolean;
  };

  const metadataFields = [
    ['authors', 'Authors'],
    ['journal', 'Journal'],
    ['conference', 'Conference'],
    ['year', 'Year'],
    ['doi', 'DOI'],
    ['status', 'Status'],
    ['tags', 'Tags'],
    ['category', 'Category']
  ] as const;

  let {
    content,
    objectTitle,
    compact = false,
    showMetadata = true
  }: Props = $props();
  let rendered = $derived(renderMarkdownPreview(content));
  let title = $derived(rendered.metadata.title || objectTitle);

  function fieldValue(key: string): string {
    return rendered.metadata[key]?.trim() || 'Not set';
  }
</script>

<div class:compact class="markdown-reader">
  {#if showMetadata && Object.keys(rendered.metadata).length}
    <section class="metadata-card" aria-label="Document metadata">
      <div class="metadata-title">
        <p>Reading Note</p>
        <h1>{title}</h1>
      </div>
      <dl>
        {#each metadataFields as [key, label]}
          <div>
            <dt>{label}</dt>
            <dd class:empty-value={fieldValue(key) === 'Not set'}>
              {fieldValue(key)}
            </dd>
          </div>
        {/each}
      </dl>
    </section>
  {/if}

  <article class="markdown-preview">
    {@html rendered.html}
  </article>
</div>

<style>
  .markdown-reader {
    margin: 0 auto;
    width: min(100%, 980px);
    padding: 2rem 2.5rem 4rem;
  }

  .markdown-reader.compact {
    width: min(100%, 860px);
    padding: 1.5rem 2rem 3rem;
  }

  .metadata-card {
    margin-bottom: 2rem;
    border: 1px solid hsl(var(--border));
    border-radius: 8px;
    background:
      linear-gradient(
        180deg,
        hsl(var(--muted) / 0.34),
        hsl(var(--background) / 0.42)
      ),
      hsl(var(--background) / 0.72);
    padding: 1.2rem;
  }

  .metadata-title p {
    color: hsl(var(--accent));
    font-size: 0.72rem;
    font-weight: 650;
    letter-spacing: 0.08em;
    margin: 0 0 0.35rem;
    text-transform: uppercase;
  }

  .metadata-title h1 {
    color: hsl(var(--foreground));
    font-size: 1.35rem;
    font-weight: 650;
    line-height: 1.25;
    margin: 0;
  }

  .metadata-card dl {
    display: grid;
    gap: 0.75rem 1rem;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    margin: 1.1rem 0 0;
  }

  .metadata-card div {
    min-width: 0;
  }

  .metadata-card dt {
    color: hsl(var(--muted-foreground));
    font-size: 0.68rem;
    font-weight: 650;
    margin-bottom: 0.2rem;
    text-transform: uppercase;
  }

  .metadata-card dd {
    color: hsl(var(--foreground));
    font-size: 0.88rem;
    line-height: 1.35;
    margin: 0;
    overflow-wrap: anywhere;
  }

  .metadata-card dd.empty-value {
    color: hsl(var(--muted-foreground) / 0.58);
  }

  :global(.markdown-preview) {
    color: hsl(var(--foreground));
    font-size: 0.98rem;
    line-height: 1.78;
  }

  :global(.markdown-preview > *:first-child) {
    margin-top: 0;
  }

  :global(.markdown-preview h1),
  :global(.markdown-preview h2),
  :global(.markdown-preview h3),
  :global(.markdown-preview h4) {
    color: hsl(var(--foreground));
    font-weight: 680;
    letter-spacing: 0;
    line-height: 1.22;
  }

  :global(.markdown-preview h1) {
    border-bottom: 1px solid hsl(var(--border));
    font-size: 2rem;
    margin: 2.35rem 0 1rem;
    padding-bottom: 0.7rem;
  }

  :global(.markdown-preview h2) {
    font-size: 1.45rem;
    margin: 2.1rem 0 0.75rem;
  }

  :global(.markdown-preview h3) {
    color: hsl(var(--foreground) / 0.92);
    font-size: 1.13rem;
    margin: 1.65rem 0 0.55rem;
  }

  :global(.markdown-preview h4) {
    color: hsl(var(--muted-foreground));
    font-size: 1rem;
    margin: 1.35rem 0 0.45rem;
  }

  :global(.markdown-preview p) {
    margin: 0.8rem 0;
  }

  :global(.markdown-preview a) {
    color: hsl(var(--accent));
    text-decoration: none;
  }

  :global(.markdown-preview a:hover) {
    text-decoration: underline;
  }

  :global(.markdown-preview strong) {
    color: hsl(var(--foreground));
    font-weight: 700;
  }

  :global(.markdown-preview em) {
    color: hsl(var(--foreground) / 0.9);
  }

  :global(.markdown-preview ul),
  :global(.markdown-preview ol) {
    margin: 0.75rem 0 1rem 1.25rem;
    padding: 0;
  }

  :global(.markdown-preview li) {
    margin: 0.35rem 0;
    padding-left: 0.25rem;
  }

  :global(.markdown-preview .task-list-item) {
    align-items: flex-start;
    display: flex;
    gap: 0.55rem;
    list-style: none;
    margin-left: -1.25rem;
  }

  :global(.markdown-preview .task-list-item input) {
    accent-color: hsl(var(--accent));
    margin-top: 0.42rem;
  }

  :global(.markdown-preview blockquote) {
    border-left: 3px solid hsl(var(--accent) / 0.6);
    color: hsl(var(--foreground) / 0.82);
    margin: 1.2rem 0;
    padding: 0.2rem 0 0.2rem 1rem;
  }

  :global(.markdown-preview code) {
    border: 1px solid hsl(var(--border));
    border-radius: 5px;
    background: hsl(var(--muted) / 0.72);
    color: hsl(var(--foreground));
    font-family:
      ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.86em;
    padding: 0.12rem 0.32rem;
  }

  :global(.markdown-preview pre.code-block) {
    border: 1px solid hsl(var(--border));
    border-radius: 8px;
    background: hsl(240 7% 5%);
    margin: 1.3rem 0;
    overflow: auto;
    max-width: 100%;
    padding: 1rem;
  }

  :global(.markdown-preview pre.code-block code) {
    border: 0;
    background: transparent;
    display: block;
    font-size: 0.86rem;
    line-height: 1.65;
    padding: 0;
  }

  :global(.markdown-preview .table-scroll) {
    margin: 1.25rem 0;
    max-width: 100%;
    overflow-x: auto;
  }

  :global(.markdown-preview table) {
    border-collapse: collapse;
    min-width: 100%;
  }

  :global(.markdown-preview th),
  :global(.markdown-preview td) {
    border: 1px solid hsl(var(--border));
    padding: 0.58rem 0.75rem;
    text-align: left;
    vertical-align: top;
  }

  :global(.markdown-preview th) {
    background: hsl(var(--muted) / 0.62);
    color: hsl(var(--foreground));
    font-size: 0.78rem;
    font-weight: 650;
    text-transform: uppercase;
  }

  :global(.markdown-preview td) {
    color: hsl(var(--foreground) / 0.86);
  }

  :global(.markdown-preview .callout) {
    border: 1px solid hsl(var(--border));
    border-left: 3px solid hsl(var(--accent));
    border-radius: 8px;
    background: hsl(var(--muted) / 0.35);
    margin: 1.25rem 0;
    padding: 0.85rem 1rem;
  }

  :global(.markdown-preview .callout-title) {
    color: hsl(var(--foreground));
    font-size: 0.78rem;
    font-weight: 720;
    margin-bottom: 0.3rem;
    text-transform: uppercase;
  }

  :global(.markdown-preview .callout-body > *:last-child) {
    margin-bottom: 0;
  }

  :global(.markdown-preview .wikilink) {
    border: 1px solid hsl(var(--accent) / 0.22);
    border-radius: 999px;
    background: hsl(var(--accent) / 0.1);
    color: hsl(var(--accent));
    display: inline-flex;
    font-size: 0.92em;
    line-height: 1.45;
    padding: 0 0.42rem;
  }

  :global(.markdown-preview figure) {
    margin: 1.35rem 0;
  }

  :global(.markdown-preview img) {
    border: 1px solid hsl(var(--border));
    border-radius: 8px;
    display: block;
    height: auto;
    max-width: 100%;
  }

  :global(.markdown-preview figcaption) {
    color: hsl(var(--muted-foreground));
    font-size: 0.8rem;
    margin-top: 0.45rem;
    text-align: center;
  }

  :global(.markdown-preview .math-inline) {
    color: hsl(var(--foreground));
  }

  :global(.markdown-preview .math-block) {
    margin: 1.4rem 0;
    max-width: 100%;
    overflow-x: auto;
    padding: 0.4rem 0;
  }

  @media (max-width: 720px) {
    .markdown-reader,
    .markdown-reader.compact {
      padding: 1.2rem 1rem 2.5rem;
    }

    :global(.markdown-preview) {
      font-size: 0.94rem;
      line-height: 1.7;
    }

    :global(.markdown-preview h1) {
      font-size: 1.55rem;
    }

    :global(.markdown-preview h2) {
      font-size: 1.25rem;
    }
  }
</style>
