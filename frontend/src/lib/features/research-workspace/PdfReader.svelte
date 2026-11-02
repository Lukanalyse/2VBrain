<script lang="ts">
  import { onMount, tick } from 'svelte';
  import type { PDFDocumentProxy } from 'pdfjs-dist';
  import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
  import 'pdfjs-dist/web/pdf_viewer.css';
  import PdfPage from './PdfPage.svelte';
  import {
    highlightColors,
    highlightValue,
    pdfHighlights,
    type HighlightColor,
    type PdfHighlight
  } from './pdfHighlights';

  let {
    objectId,
    title,
    url
  }: { objectId: string; title: string; url: string } = $props();
  let root: HTMLDivElement;
  let viewport: HTMLDivElement;
  let document = $state<PDFDocumentProxy | null>(null);
  let highlights = $state<PdfHighlight[]>([]);
  let color = $state<HighlightColor>('yellow');
  let loading = $state(true);
  let saving = $state(false);
  let error = $state('');
  let availableWidth = $state(740);
  let zoom = $state(1);
  let selectedText = $state('');
  let activeHighlight = $state<string | null>(null);
  let highlightMenu = $state<HTMLDetailsElement>();
  let navigation = 0;
  let pending = $state<{ page: number; rects: PdfHighlight['rects'] }[]>([]);
  const pageWidth = $derived(Math.max(200, availableWidth - 32) * zoom);

  onMount(() => {
    let disposed = false;
    let task: { destroy(): Promise<void> } | undefined;
    const observer = new ResizeObserver(([entry]) => {
      availableWidth = entry.contentRect.width;
    });
    observer.observe(viewport);
    void (async () => {
      try {
        const pdfjs = await import('pdfjs-dist');
        if (disposed) return;
        pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;
        const resourceUrl = (directory: string) =>
          new URL(`/pdfjs/${directory}/`, window.location.href).href;
        const loadingTask = pdfjs.getDocument({
          url: url.split('#')[0],
          wasmUrl: resourceUrl('wasm'),
          cMapUrl: resourceUrl('cmaps'),
          standardFontDataUrl: resourceUrl('standard_fonts'),
          iccUrl: resourceUrl('iccs'),
          // The local JS decoders also work under the desktop app's strict CSP.
          useWasm: false
        });
        task = loadingTask;
        const [pdf, marks] = await Promise.all([
          loadingTask.promise,
          pdfHighlights(objectId)
        ]);
        if (disposed) return;
        document = pdf;
        highlights = marks;
        loading = false;
        const page = Number(
          new URLSearchParams(url.split('#')[1] ?? '').get('page')
        );
        if (page > 1)
          requestAnimationFrame(() =>
            root
              .querySelector(`[data-pdf-page="${page}"]`)
              ?.scrollIntoView({ block: 'start' })
          );
      } catch (cause) {
        if (!disposed) {
          error =
            cause instanceof Error ? cause.message : 'Unable to load PDF.';
          loading = false;
        }
      }
    })();
    return () => {
      disposed = true;
      navigation++;
      observer.disconnect();
      void task?.destroy();
    };
  });

  async function goToHighlight(mark: PdfHighlight): Promise<void> {
    const request = ++navigation;
    activeHighlight = mark.id;
    if (highlightMenu) highlightMenu.open = false;
    await tick();
    const page = root.querySelector<HTMLElement>(
      `[data-pdf-page="${mark.page}"]`
    );
    if (!page) return;
    // Bringing the page into view starts its lazy rendering and determines its
    // actual aspect ratio. Center the saved rectangle after that render settles.
    page.scrollIntoView({ block: 'center' });
    const rect = mark.rects[0];
    if (!rect) return;
    const center = () => {
      const bounds = page.getBoundingClientRect();
      const area = viewport.getBoundingClientRect();
      viewport.scrollTo({
        top:
          viewport.scrollTop +
          bounds.top -
          area.top +
          (rect.y + rect.height / 2) * bounds.height -
          viewport.clientHeight / 2,
        left:
          viewport.scrollLeft +
          bounds.left -
          area.left +
          (rect.x + rect.width / 2) * bounds.width -
          viewport.clientWidth / 2,
        behavior: 'instant'
      });
    };
    center();
    // Cancellation keeps a later click or manual scroll in control.
    const stop = () => {
      if (navigation === request) navigation++;
    };
    viewport.addEventListener('wheel', stop, { once: true, passive: true });
    viewport.addEventListener('pointerdown', stop, { once: true });
    try {
      for (
        let attempt = 0;
        attempt < 100 && navigation === request;
        attempt++
      ) {
        if (page.dataset.rendered === 'true') {
          center();
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 50));
      }
    } finally {
      viewport.removeEventListener('wheel', stop);
      viewport.removeEventListener('pointerdown', stop);
    }
  }

  function captureSelection(): void {
    const selection = window.getSelection();
    selectedText = '';
    pending = [];
    if (!selection || selection.isCollapsed || !selection.rangeCount) return;
    if (
      !viewport.contains(selection.anchorNode) ||
      !viewport.contains(selection.focusNode)
    )
      return;
    const range = selection.getRangeAt(0);
    const fragments: typeof pending = [];
    for (const page of viewport.querySelectorAll<HTMLElement>(
      '[data-pdf-page]'
    )) {
      const bounds = page.getBoundingClientRect();
      const rects = Array.from(
        page.querySelectorAll('.textLayer span')
      ).flatMap((span) => {
        if (span.children.length || !range.intersectsNode(span)) return [];
        const part = window.document.createRange();
        part.selectNodeContents(span);
        if (span.contains(range.startContainer))
          part.setStart(range.startContainer, range.startOffset);
        if (span.contains(range.endContainer))
          part.setEnd(range.endContainer, range.endOffset);
        return Array.from(part.getClientRects()).filter(
          (rect) => rect.width > 1 && rect.height > 1
        );
      });
      const clipped = rects.flatMap((rect) => {
        const left = Math.max(rect.left, bounds.left),
          top = Math.max(rect.top, bounds.top);
        const right = Math.min(rect.right, bounds.right),
          bottom = Math.min(rect.bottom, bounds.bottom);
        return right > left && bottom > top
          ? [
              {
                x: (left - bounds.left) / bounds.width,
                y: (top - bounds.top) / bounds.height,
                width: (right - left) / bounds.width,
                height: (bottom - top) / bounds.height
              }
            ]
          : [];
      });
      if (clipped.length)
        fragments.push({ page: Number(page.dataset.pdfPage), rects: clipped });
    }
    if (fragments.length) {
      selectedText = selection.toString().trim();
      pending = fragments;
    }
  }

  async function persist(next: PdfHighlight[]): Promise<void> {
    if (saving) return;
    saving = true;
    error = '';
    try {
      highlights = await pdfHighlights(objectId, next);
    } catch (cause) {
      error =
        cause instanceof Error ? cause.message : 'Unable to save highlights.';
    } finally {
      saving = false;
    }
  }

  async function highlight(): Promise<void> {
    captureSelection();
    if (!document || !selectedText || !pending.length || saving) return;
    await persist([
      ...highlights,
      ...pending.map((fragment) => ({
        ...fragment,
        id: crypto.randomUUID(),
        color,
        text: selectedText.slice(0, 50000)
      }))
    ]);
    if (!error) {
      window.getSelection()?.removeAllRanges();
      selectedText = '';
      pending = [];
    }
  }

  function shortcut(event: KeyboardEvent): void {
    if (
      (event.metaKey || event.ctrlKey) &&
      event.shiftKey &&
      event.key.toLowerCase() === 'h'
    ) {
      captureSelection();
      if (pending.length) {
        event.preventDefault();
        void highlight();
      }
    }
  }
</script>

<svelte:window onkeydown={shortcut} />
<svelte:document onselectionchange={captureSelection} />

<div bind:this={root} class="pdf-reader">
  <div class="pdf-tools" aria-label="PDF tools">
    <div class="colors" role="group" aria-label="Highlight color">
      {#each highlightColors as option}
        <button
          type="button"
          class="swatch"
          class:active={color === option.id}
          style={`background:${option.value}`}
          title={option.label}
          aria-label={option.label}
          aria-pressed={color === option.id}
          onpointerdown={(event) => event.preventDefault()}
          onclick={() => (color = option.id)}
        ></button>
      {/each}
    </div>
    <button
      class="ros-btn-ghost"
      type="button"
      disabled={!selectedText || saving || !document}
      title="Highlight selection (⌘⇧H / Ctrl+Shift+H)"
      onpointerdown={(event) => event.preventDefault()}
      onclick={highlight}>Highlight <kbd>⌘⇧H</kbd></button
    >
    <button
      class="ros-btn-ghost"
      type="button"
      aria-label="Zoom out"
      onclick={() => {
        zoom = Math.max(0.5, zoom - 0.25);
      }}>−</button
    >
    <span>{Math.round(zoom * 100)}%</span>
    <button
      class="ros-btn-ghost"
      type="button"
      aria-label="Zoom in"
      onclick={() => {
        zoom = Math.min(3, zoom + 0.25);
      }}>+</button
    >
    <a
      class="ros-btn-ghost"
      href={url}
      target="_blank"
      rel="noreferrer"
      title="Open original PDF">↗</a
    >
    <span aria-live="polite">{saving ? 'Saving…' : ''}</span>
    {#if highlights.length}
      <details bind:this={highlightMenu}>
        <summary>Highlights ({highlights.length})</summary>
        <ul>
          {#each highlights as mark (mark.id)}
            <li>
              <button
                type="button"
                class="highlight-link"
                aria-label={`Go to highlight on page ${mark.page}: ${mark.text.slice(0, 80)}`}
                onclick={() => goToHighlight(mark)}
              >
                <span style={`color:${highlightValue(mark.color)}`}>●</span>
                p. {mark.page} · {mark.text.slice(0, 80)}
              </button>
              <button
                type="button"
                class="ros-btn-ghost"
                disabled={saving}
                aria-label={`Delete highlight on page ${mark.page}`}
                onclick={() =>
                  persist(highlights.filter((item) => item.id !== mark.id))}
                >×</button
              >
            </li>
          {/each}
        </ul>
      </details>
    {/if}
  </div>
  {#if error}<p class="reader-message" role="alert">{error}</p>{/if}
  <div bind:this={viewport} class="pdf-viewport" aria-label={title}>
    {#if loading}<p class="reader-message">Loading PDF…</p>
    {:else if document}
      <div class="pdf-pages" style={`min-width:${pageWidth + 32}px`}>
        {#each Array.from({ length: document.numPages }, (_, index) => index + 1) as pageNumber}
          <PdfPage
            {document}
            {pageNumber}
            width={pageWidth}
            {highlights}
            {activeHighlight}
          />
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .pdf-reader {
    display: flex;
    flex-direction: column;
    flex: 1;
    width: 100%;
    height: 100%;
    min-height: 0;
    overflow: hidden;
  }
  .pdf-tools {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    padding: 8px 12px;
    border-bottom: 1px solid hsl(var(--border));
    font-size: 11px;
  }
  .colors {
    display: flex;
    gap: 6px;
    padding: 4px;
  }
  .swatch {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    border: 2px solid transparent;
  }
  .swatch.active {
    outline: 2px solid hsl(var(--foreground));
    outline-offset: 2px;
  }
  kbd {
    margin-left: 6px;
    opacity: 0.65;
  }
  .pdf-viewport {
    flex: 1;
    min-height: 0;
    overflow: auto;
    background: hsl(var(--muted) / 0.15);
  }
  .pdf-pages {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    padding: 16px;
  }
  .reader-message {
    padding: 12px;
    font-size: 12px;
  }
  details {
    position: relative;
  }
  summary {
    cursor: pointer;
  }
  ul {
    position: absolute;
    right: 0;
    top: 24px;
    z-index: 10;
    width: 300px;
    max-height: 260px;
    overflow: auto;
    padding: 12px;
    border: 1px solid hsl(var(--border));
    background: hsl(var(--surface));
    border-radius: 8px;
  }
  .highlight-link {
    flex: 1;
    min-width: 0;
    text-align: left;
    padding: 4px;
    border-radius: 4px;
  }
  .highlight-link:hover,
  .highlight-link:focus-visible {
    background: hsl(var(--muted) / 0.4);
  }
  li {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 8px;
  }
</style>
