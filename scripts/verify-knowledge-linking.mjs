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
const paperNames = ['Phase Seven Paper A.pdf', 'Phase Seven Paper B.pdf'];
const conceptNames = ['Phase Seven Concept A', 'Phase Seven Concept B'];
const projectName = 'Phase Seven Project';
const brainstormName = 'Phase Seven Brainstorm';

async function fetchJson(url, init) {
  const response = await fetch(url, init);
  if (!response.ok) throw new Error(`Request failed ${url}: ${response.status} ${await response.text()}`);
  return response.json();
}

async function storage() {
  return fetchJson(`${apiUrl}/storage`);
}

async function cleanup() {
  const items = (await fetchJson(`${apiUrl}/library`).catch(() => ({ items: [] }))).items;
  for (const item of items.filter((entry) => paperNames.includes(entry.original_filename))) {
    await fs.rm(item.file_path, { force: true }).catch(() => undefined);
    await fs.rm(item.markdown_path, { force: true }).catch(() => undefined);
  }

  const status = await storage().catch(() => null);
  if (status?.vault_path) {
    for (const concept of conceptNames) {
      await fs.rm(path.join(status.vault_path, '03 Knowledge', `${concept}.md`), { force: true }).catch(() => undefined);
    }
    await fs.rm(path.join(status.vault_path, '01 Projects', `${projectName}.md`), { force: true }).catch(() => undefined);
    await fs.rm(path.join(status.vault_path, '04 Brainstorm', `${brainstormName}.md`), { force: true }).catch(() => undefined);
  }

  const db = new DatabaseSync(path.join(rootDir, 'backend', 'research_os.db'));
  db.prepare(
    "delete from library_items where original_filename in ('Phase Seven Paper A.pdf', 'Phase Seven Paper B.pdf')"
  ).run();
  db.close();
}

async function makePdf(filePath) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, Buffer.from('%PDF-1.7\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n'));
}

async function uploadPaper(filename) {
  const pdfPath = path.join('/tmp/research-os-phase7-linking', filename);
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
      category: 'Phase 7',
      tags: ['phase7']
    })
  });
}

async function setup() {
  await cleanup();
  const [paperA, paperB] = await Promise.all(paperNames.map(uploadPaper));
  const [conceptA, conceptB] = await Promise.all(conceptNames.map(createConcept));
  const status = await storage();
  await fs.mkdir(path.join(status.vault_path, '01 Projects'), { recursive: true });
  await fs.mkdir(path.join(status.vault_path, '04 Brainstorm'), { recursive: true });
  await fs.writeFile(path.join(status.vault_path, '01 Projects', `${projectName}.md`), '# Notes\n', 'utf8');
  await fs.writeFile(path.join(status.vault_path, '04 Brainstorm', `${brainstormName}.md`), '# Notes\n', 'utf8');
  return { paperA, paperB, conceptA, conceptB, vaultPath: status.vault_path };
}

async function linkVisibleResult(page, query, expectedLabel) {
  await page.getByPlaceholder('Search papers, concepts, projects, brainstorm notes, reviews').fill(query);
  await page.getByText(expectedLabel).first().waitFor();
  await page.locator('label').filter({ hasText: expectedLabel }).first().getByRole('checkbox').check();
  await page.getByRole('button', { name: 'Link', exact: true }).click();
  await page.getByText('Links saved in Markdown.').waitFor();
}

async function main() {
  const fixtures = await setup();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  try {
    await page.goto(`${frontendUrl}knowledge/${fixtures.paperA.id}`, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'Relations' }).click();
    await linkVisibleResult(page, 'Phase Seven Paper B', 'Phase Seven Paper B');
    await linkVisibleResult(page, 'Phase Seven Concept A', 'Phase Seven Concept A');

    await page.goto(`${frontendUrl}knowledge/concepts/${encodeURIComponent(conceptNames[0])}`, { waitUntil: 'networkidle' });
    await linkVisibleResult(page, projectName, projectName);

    await page.goto(`${frontendUrl}brainstorm`, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: new RegExp(brainstormName) }).click();
    await linkVisibleResult(page, 'Phase Seven Concept', 'Phase Seven Concept A');
    await linkVisibleResult(page, 'Phase Seven Concept B', 'Phase Seven Concept B');

    const paperMarkdown = await fs.readFile(fixtures.paperA.markdown_path, 'utf8');
    const conceptMarkdown = await fs.readFile(fixtures.conceptA.markdown_path, 'utf8');
    const brainstormMarkdown = await fs.readFile(
      path.join(fixtures.vaultPath, '04 Brainstorm', `${brainstormName}.md`),
      'utf8'
    );

    if (!paperMarkdown.includes('[[Phase Seven Paper B]]')) throw new Error('Paper to Paper link missing.');
    if (!paperMarkdown.includes('[[Phase Seven Concept A]]')) throw new Error('Paper to Concept link missing.');
    if (!conceptMarkdown.includes(`[[${projectName}]]`)) throw new Error('Concept to Project link missing.');
    if (!brainstormMarkdown.includes('[[Phase Seven Concept A]]')) throw new Error('Brainstorm to Concept A link missing.');
    if (!brainstormMarkdown.includes('[[Phase Seven Concept B]]')) throw new Error('Brainstorm to Concept B link missing.');

    console.log('Knowledge Linking verification passed.');
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
