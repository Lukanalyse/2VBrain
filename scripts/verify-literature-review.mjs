import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';
import { DatabaseSync } from 'node:sqlite';

const rootDir = process.cwd();
const require = createRequire(path.join(rootDir, 'frontend', 'package.json'));
const { chromium } = require('@playwright/test');

const frontendUrl = 'http://127.0.0.1:5173/';
const apiUrl = 'http://127.0.0.1:8000/api/v1';
const pdfDir = '/tmp/research-os-phase9-review';
const reviewTitle = 'Phase Nine Literature Review';
const paperNames = ['Phase Nine Review Paper A.pdf', 'Phase Nine Review Paper B.pdf'];
const conceptNames = ['Phase Nine Review Concept A', 'Phase Nine Review Concept B'];
const synthesis = 'This synthesis connects two papers and two concepts for the literature review.';

async function fetchJson(url, init) {
  const response = await fetch(url, init);
  if (!response.ok) throw new Error(`Request failed ${url}: ${response.status} ${await response.text()}`);
  return response.json();
}

async function cleanup() {
  const items = (await fetchJson(`${apiUrl}/library`).catch(() => ({ items: [] }))).items;
  for (const item of items.filter((entry) => paperNames.includes(entry.original_filename))) {
    await fs.rm(item.file_path, { force: true }).catch(() => undefined);
    await fs.rm(item.markdown_path, { force: true }).catch(() => undefined);
  }

  const storage = await fetchJson(`${apiUrl}/storage`).catch(() => null);
  if (storage?.vault_path) {
    await fs.rm(path.join(storage.vault_path, '05 Literature Reviews', `${reviewTitle}.md`), { force: true }).catch(() => undefined);
    for (const concept of conceptNames) {
      await fs.rm(path.join(storage.vault_path, '03 Knowledge', `${concept}.md`), { force: true }).catch(() => undefined);
    }
  }

  const db = new DatabaseSync(path.join(rootDir, 'backend', 'research_os.db'));
  db.prepare(
    "delete from library_items where original_filename in ('Phase Nine Review Paper A.pdf', 'Phase Nine Review Paper B.pdf')"
  ).run();
  db.close();
}

async function makePdf(filePath) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, Buffer.from('%PDF-1.7\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n'));
}

async function importPaper(filename) {
  const pdfPath = path.join(pdfDir, filename);
  await makePdf(pdfPath);
  const body = new FormData();
  body.append('file', new Blob([await fs.readFile(pdfPath)], { type: 'application/pdf' }), filename);
  body.append('title', filename.replace('.pdf', ''));
  body.append('authors', '');
  body.append('journal', '');
  body.append('conference', '');
  body.append('doi', '');
  body.append('abstract', '');
  body.append('keywords', '');
  return fetchJson(`${apiUrl}/library/import?duplicate_strategy=cancel`, {
    method: 'POST',
    body
  });
}

async function createConcept(name) {
  return fetchJson(`${apiUrl}/concepts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      description: `${name} description`,
      category: 'Literature Review',
      tags: ['phase9', 'review']
    })
  });
}

async function setup() {
  await cleanup();
  await Promise.all(paperNames.map(importPaper));
  await Promise.all(conceptNames.map(createConcept));
}

async function linkResult(page, query, label) {
  await page.getByPlaceholder('Search papers, concepts, projects, brainstorm notes, reviews').fill(query);
  await page.locator('label').filter({ hasText: label }).first().getByRole('checkbox').check();
  await page.getByRole('button', { name: 'Link', exact: true }).click();
  await page.getByText('Links saved in Markdown.').waitFor();
}

async function main() {
  await setup();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  try {
    await page.goto(`${frontendUrl}reviews`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Literature Reviews' }).waitFor();
    await page.getByLabel('New Literature Review').fill(reviewTitle);
    await page.getByRole('button', { name: 'Create' }).click();
    await page.getByRole('heading', { name: reviewTitle }).first().waitFor();

    await page.getByRole('button', { name: 'Papers' }).click();
    await linkResult(page, 'Phase Nine Review Paper A', 'Phase Nine Review Paper A');
    await linkResult(page, 'Phase Nine Review Paper B', 'Phase Nine Review Paper B');

    await page.getByRole('button', { name: 'Concepts' }).click();
    await linkResult(page, 'Phase Nine Review Concept A', 'Phase Nine Review Concept A');
    await linkResult(page, 'Phase Nine Review Concept B', 'Phase Nine Review Concept B');

    await page.getByRole('button', { name: 'Writing' }).click();
    const editor = page.locator('textarea').first();
    const current = await editor.inputValue();
    const saveResponse = page.waitForResponse(
      (response) =>
        response.url().includes('/api/v1/literature-reviews/') &&
        response.request().method() === 'PUT'
    );
    await editor.fill(`${current}\n${synthesis}\n`);
    const response = await saveResponse;
    if (!response.ok()) throw new Error(`Review save failed: ${response.status()}`);
    await page.getByText('Saved').waitFor({ timeout: 5000 });

    await page.goto(frontendUrl, { waitUntil: 'networkidle' });
    await page.getByPlaceholder('Search papers, concepts, projects, brainstorm, reviews').first().fill(reviewTitle);
    await page.getByText(reviewTitle).first().waitFor();
    await page.goto(`${frontendUrl}reviews?selected=review:${encodeURIComponent(reviewTitle)}`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: reviewTitle }).first().waitFor();
    await page.getByRole('button', { name: 'Writing' }).click();
    const reopenedValue = await page.locator('textarea').first().inputValue();
    if (!reopenedValue.includes(synthesis)) {
      throw new Error('Saved synthesis was not restored in the Writing editor.');
    }

    const storage = await fetchJson(`${apiUrl}/storage`);
    const reviewMarkdown = await fs.readFile(
      path.join(storage.vault_path, '05 Literature Reviews', `${reviewTitle}.md`),
      'utf8'
    );

    for (const expected of [
      '[[Phase Nine Review Paper A]]',
      '[[Phase Nine Review Paper B]]',
      '[[Phase Nine Review Concept A]]',
      '[[Phase Nine Review Concept B]]',
      synthesis
    ]) {
      if (!reviewMarkdown.includes(expected)) {
        throw new Error(`Review Markdown missing: ${expected}`);
      }
    }

    console.log('Literature Review verification passed.');
  } finally {
    await browser.close();
    await cleanup();
  }
}

main().catch(async (error) => {
  console.error(error);
  await cleanup().catch(() => undefined);
  process.exit(1);
});
