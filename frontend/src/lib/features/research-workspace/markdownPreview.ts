import katex from 'katex';

export type Frontmatter = Record<string, string>;

export type RenderedMarkdown = {
  metadata: Frontmatter;
  html: string;
};

type RenderState = {
  placeholders: string[];
};

const placeholderStart = '\uE000';
const placeholderEnd = '\uE001';

export function renderMarkdownPreview(content: string): RenderedMarkdown {
  const { metadata, body } = splitFrontmatter(content);
  const state: RenderState = { placeholders: [] };
  const prepared = protectBlocks(body.replace(/\r\n/g, '\n'), state);
  const html = restorePlaceholders(renderBlocks(prepared, state), state);

  return { metadata, html };
}

function splitFrontmatter(content: string): {
  metadata: Frontmatter;
  body: string;
} {
  const normalized = content.replace(/\r\n/g, '\n');
  const match = normalized.match(/^---\n([\s\S]*?)\n---\n?/);
  if (!match) return { metadata: {}, body: normalized };

  return {
    metadata: parseFrontmatter(match[1]),
    body: normalized.slice(match[0].length)
  };
}

function parseFrontmatter(source: string): Frontmatter {
  const metadata: Frontmatter = {};
  for (const line of source.split('\n')) {
    const match = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!match) continue;

    const [, key, rawValue] = match;
    const value = rawValue
      .replace(/^["']|["']$/g, '')
      .replace(/^\[(.*)\]$/, '$1')
      .trim();
    metadata[key] = value;
  }
  return metadata;
}

function protectBlocks(source: string, state: RenderState): string {
  let output = source.replace(
    /```([A-Za-z0-9_-]+)?\n([\s\S]*?)```/g,
    (_match, language: string, code: string) => {
      const lang = language ? ` data-language="${escapeHtml(language)}"` : '';
      return reserve(
        `<pre class="code-block"${lang}><code>${escapeHtml(code.trimEnd())}</code></pre>`,
        state
      );
    }
  );

  output = output.replace(/\$\$([\s\S]+?)\$\$/g, (_match, expression: string) =>
    reserve(
      `<div class="math-block">${renderLatex(expression.trim(), true)}</div>`,
      state
    )
  );

  return output;
}

function renderBlocks(source: string, state: RenderState): string {
  const lines = source.split('\n');
  const blocks: string[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }

    if (isPlaceholderLine(line)) {
      blocks.push(line.trim());
      index += 1;
      continue;
    }

    const table = readTable(lines, index, state);
    if (table) {
      blocks.push(table.html);
      index = table.nextIndex;
      continue;
    }

    const callout = readCallout(lines, index, state);
    if (callout) {
      blocks.push(callout.html);
      index = callout.nextIndex;
      continue;
    }

    const quote = readBlockquote(lines, index, state);
    if (quote) {
      blocks.push(quote.html);
      index = quote.nextIndex;
      continue;
    }

    const list = readList(lines, index, state);
    if (list) {
      blocks.push(list.html);
      index = list.nextIndex;
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      const level = heading[1].length;
      blocks.push(`<h${level}>${renderInline(heading[2], state)}</h${level}>`);
      index += 1;
      continue;
    }

    const paragraphLines = [line.trim()];
    index += 1;
    while (
      index < lines.length &&
      lines[index].trim() &&
      !startsBlock(lines[index]) &&
      !isTableStart(lines, index)
    ) {
      paragraphLines.push(lines[index].trim());
      index += 1;
    }
    blocks.push(`<p>${renderInline(paragraphLines.join(' '), state)}</p>`);
  }

  return blocks.join('\n');
}

function readTable(
  lines: string[],
  index: number,
  state: RenderState
): { html: string; nextIndex: number } | null {
  if (!isTableStart(lines, index)) return null;

  const rows: string[][] = [];
  let cursor = index;
  while (
    cursor < lines.length &&
    lines[cursor].includes('|') &&
    lines[cursor].trim()
  ) {
    if (cursor !== index + 1) rows.push(splitTableRow(lines[cursor]));
    cursor += 1;
  }

  const [head, ...bodyRows] = rows;
  const headHtml = head
    .map((cell) => `<th>${renderInline(cell, state)}</th>`)
    .join('');
  const bodyHtml = bodyRows
    .map(
      (row) =>
        `<tr>${row.map((cell) => `<td>${renderInline(cell, state)}</td>`).join('')}</tr>`
    )
    .join('');

  return {
    html: `<div class="table-scroll"><table><thead><tr>${headHtml}</tr></thead><tbody>${bodyHtml}</tbody></table></div>`,
    nextIndex: cursor
  };
}

function isTableStart(lines: string[], index: number): boolean {
  const header = lines[index];
  const separator = lines[index + 1];
  return Boolean(
    header?.includes('|') &&
    /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(separator ?? '')
  );
}

function splitTableRow(row: string): string[] {
  return row
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => cell.trim());
}

function readCallout(
  lines: string[],
  index: number,
  state: RenderState
): { html: string; nextIndex: number } | null {
  const match = lines[index].match(/^>\s*\[!(\w+)\]\s*(.*)$/);
  if (!match) return null;

  const [, type, title] = match;
  const body: string[] = [];
  let cursor = index + 1;
  while (cursor < lines.length && lines[cursor].startsWith('>')) {
    body.push(lines[cursor].replace(/^>\s?/, ''));
    cursor += 1;
  }

  return {
    html: `<aside class="callout callout-${type.toLowerCase()}"><div class="callout-title">${escapeHtml(type.toUpperCase())}${title ? ` · ${renderInline(title, state)}` : ''}</div>${body.length ? `<div class="callout-body">${renderBlocks(body.join('\n'), state)}</div>` : ''}</aside>`,
    nextIndex: cursor
  };
}

function readBlockquote(
  lines: string[],
  index: number,
  state: RenderState
): { html: string; nextIndex: number } | null {
  if (!lines[index].startsWith('>')) return null;

  const body: string[] = [];
  let cursor = index;
  while (cursor < lines.length && lines[cursor].startsWith('>')) {
    body.push(lines[cursor].replace(/^>\s?/, ''));
    cursor += 1;
  }

  return {
    html: `<blockquote>${renderBlocks(body.join('\n'), state)}</blockquote>`,
    nextIndex: cursor
  };
}

function readList(
  lines: string[],
  index: number,
  state: RenderState
): { html: string; nextIndex: number } | null {
  const first = lines[index];
  const unordered = /^\s*[-*]\s+/.test(first);
  const ordered = /^\s*\d+\.\s+/.test(first);
  if (!unordered && !ordered) return null;

  const items: string[] = [];
  let cursor = index;
  while (
    cursor < lines.length &&
    (unordered
      ? /^\s*[-*]\s+/.test(lines[cursor])
      : /^\s*\d+\.\s+/.test(lines[cursor]))
  ) {
    const text = lines[cursor].replace(
      unordered ? /^\s*[-*]\s+/ : /^\s*\d+\.\s+/,
      ''
    );
    const task = text.match(/^\[( |x|X)\]\s+(.+)$/);
    if (task) {
      const checked = task[1].toLowerCase() === 'x';
      items.push(
        `<li class="task-list-item"><input type="checkbox" disabled${checked ? ' checked' : ''} /> <span>${renderInline(task[2], state)}</span></li>`
      );
    } else {
      items.push(`<li>${renderInline(text, state)}</li>`);
    }
    cursor += 1;
  }

  return {
    html: unordered
      ? `<ul>${items.join('')}</ul>`
      : `<ol>${items.join('')}</ol>`,
    nextIndex: cursor
  };
}

function startsBlock(line: string): boolean {
  return (
    /^#{1,6}\s+/.test(line) ||
    /^>\s?/.test(line) ||
    /^\s*[-*]\s+/.test(line) ||
    /^\s*\d+\.\s+/.test(line) ||
    isPlaceholderLine(line)
  );
}

function renderInline(source: string, state: RenderState): string {
  let output = source.replace(/`([^`]+)`/g, (_match, code: string) =>
    reserve(`<code>${escapeHtml(code)}</code>`, state)
  );

  // Reserve inline math BEFORE HTML-escaping so LaTeX control characters
  // (`<`, `>`, `&`, `_`, `^`, `\\`) reach KaTeX intact. Escaping first would
  // turn the `&` alignment separators of matrices/align into `&amp;` and break
  // the render. The reserved placeholder then survives escapeHtml() untouched.
  output = output.replace(
    /(^|[^\\$])\$(?!\$)([^$\n]+?)\$(?!\$)/g,
    (_match, prefix: string, expression: string) =>
      `${prefix}${reserve(`<span class="math-inline">${renderLatex(expression.trim(), false)}</span>`, state)}`
  );

  output = escapeHtml(output);
  output = output.replace(
    /!\[([^\]]*)\]\(([^)]+)\)/g,
    (_match, alt: string, src: string) => {
      const safeAlt = escapeHtml(alt);
      const safeSrc = escapeAttribute(src);
      return reserve(
        `<figure><img src="${safeSrc}" alt="${safeAlt}" loading="lazy" />${safeAlt ? `<figcaption>${safeAlt}</figcaption>` : ''}</figure>`,
        state
      );
    }
  );
  output = output.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noreferrer">$1</a>'
  );
  output = output.replace(
    /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,
    (_match, target: string, alias: string) => {
      const label = alias || target;
      return `<span class="wikilink" data-target="${escapeAttribute(target)}">${escapeHtml(label)}</span>`;
    }
  );
  output = output.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  output = output.replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');

  return output;
}

function renderLatex(expression: string, displayMode: boolean): string {
  return katex.renderToString(expression, {
    displayMode,
    throwOnError: false,
    strict: 'ignore',
    trust: false
  });
}

function reserve(html: string, state: RenderState): string {
  const index = state.placeholders.push(html) - 1;
  return `${placeholderStart}${index}${placeholderEnd}`;
}

function restorePlaceholders(source: string, state: RenderState): string {
  let output = source;
  state.placeholders.forEach((html, index) => {
    output = output.replaceAll(
      `${placeholderStart}${index}${placeholderEnd}`,
      html
    );
  });
  return output;
}

function isPlaceholderLine(line: string): boolean {
  return new RegExp(`^\\s*${placeholderStart}\\d+${placeholderEnd}\\s*$`).test(
    line
  );
}

function escapeHtml(source: string): string {
  return source
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function escapeAttribute(source: string): string {
  return escapeHtml(source).replaceAll('`', '&#096;');
}
