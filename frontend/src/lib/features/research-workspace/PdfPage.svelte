<script lang="ts">
  import { onMount } from 'svelte';
  import type { PDFDocumentProxy } from 'pdfjs-dist';
  import { highlightValue, type PdfHighlight } from './pdfHighlights';

  let {
    document,
    pageNumber,
    width,
    highlights,
    activeHighlight = null
  }: {
    document: PDFDocumentProxy;
    pageNumber: number;
    width: number;
    highlights: PdfHighlight[];
    activeHighlight?: string | null;
  } = $props();
  let host: HTMLDivElement;
  let canvas: HTMLCanvasElement;
  let text: HTMLDivElement;
  let visible = $state(false);
  let ratio = $state(1.414);
  let rendered = $state(false);
  let error = $state('');

  onMount(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          visible = true;
          observer.disconnect();
        }
      },
      { rootMargin: '800px' }
    );
    observer.observe(host);
    return () => observer.disconnect();
  });

  $effect(() => {
    if (!visible) return;
    const targetWidth = width;
    rendered = false;
    error = '';
    const pdf = document;
    const number = pageNumber;
    let cancelled = false;
    let renderTask: { cancel(): void } | undefined;
    let textLayer: { cancel(): void } | undefined;
    void (async () => {
      try {
        const { TextLayer } = await import('pdfjs-dist');
        const page = await pdf.getPage(number);
        if (cancelled) return;
        const base = page.getViewport({ scale: 1 });
        ratio = base.height / base.width;
        const viewport = page.getViewport({ scale: targetWidth / base.width });
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.ceil(viewport.width * dpr);
        canvas.height = Math.ceil(viewport.height * dpr);
        text.replaceChildren();
        host.style.setProperty('--scale-factor', String(viewport.scale));
        const task = page.render({
          canvas,
          viewport,
          transform: [dpr, 0, 0, dpr, 0, 0]
        });
        renderTask = task;
        await task.promise;
        if (cancelled) return;
        const content = await page.getTextContent();
        if (cancelled) return;
        const layer = new TextLayer({
          textContentSource: content,
          container: text,
          viewport
        });
        textLayer = layer;
        await layer.render();
        if (!cancelled) rendered = true;
      } catch (cause) {
        if (!cancelled)
          error =
            cause instanceof Error ? cause.message : 'Unable to render page.';
      }
    })();
    return () => {
      cancelled = true;
      renderTask?.cancel();
      textLayer?.cancel();
    };
  });
</script>

<div
  bind:this={host}
  class="pdf-page"
  data-pdf-page={pageNumber}
  data-rendered={rendered}
  style={`width: ${width}px; height: ${width * ratio}px;`}
>
  <canvas bind:this={canvas}></canvas>
  <div class="highlights" aria-hidden="true">
    {#each highlights.filter((mark) => mark.page === pageNumber) as mark (mark.id)}
      {#each mark.rects as rect}
        <span
          class:highlight-active={mark.id === activeHighlight}
          style={`left:${rect.x * 100}%;top:${rect.y * 100}%;width:${rect.width * 100}%;height:${rect.height * 100}%;background:${highlightValue(mark.color)}`}
        ></span>
      {/each}
    {/each}
  </div>
  <div bind:this={text} class="textLayer"></div>
  {#if error}<p role="alert" class="page-error">{error}</p>{/if}
</div>

<style>
  .pdf-page {
    position: relative;
    flex-shrink: 0;
    background: white;
    box-shadow: 0 2px 8px #0003;
    --user-unit: 1;
    --total-scale-factor: calc(var(--scale-factor) * var(--user-unit));
  }
  canvas {
    display: block;
    width: 100%;
    height: 100%;
  }
  .highlights {
    position: absolute;
    inset: 0;
    pointer-events: none;
    mix-blend-mode: multiply;
  }
  .highlights span {
    position: absolute;
    opacity: 0.4;
  }
  .highlights span.highlight-active {
    opacity: 0.65;
    outline: 2px solid #b45309;
    outline-offset: 2px;
  }
  .page-error {
    position: absolute;
    inset: 24px;
    color: #991b1b;
  }
</style>
