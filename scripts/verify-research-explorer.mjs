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
const pdfDir = '/tmp/research-os-phase10-explorer';
const paperNames = ['Phase Ten Explorer Paper A.pdf', 'Phase Ten Explorer Paper B.pdf'];
const conceptNames = ['Phase Ten Explorer Concept A', 'Phase Ten Explorer Concept B'];
const projectName = 'Phase Ten Explorer Project';
const brainstormName = 'Phase Ten Explorer Brainstorm';
const reviewName = 'Phase Ten Explorer Review';

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
    for (const concept of conceptNames) {
      await fs.rm(path.join(storage.vault_path, '03 Knowledge', `${concept}.md`), { force: true }).catch(() => undefined);
    }
    await fs.rm(path.join(storage.vault_path, '01 Projects', `${projectName}.md`), { force: true }).catch(() => undefined);
    await fs.rm(path.join(storage.vault_path, '04 Brainstorm', `${brainstormName}.md`), { force: true }).catch(() => undefined);
    await fs.rm(path.join(storage.vault_path, '05 Literature Reviews', `${reviewName}.md`), { force: true }).catch(() => undefined);
  }

  const db = new DatabaseSync(path.join(rootDir, 'backend', 'research_os.db'));
  db.prepare(
    "delete from library_items where original_filename in ('Phase Ten Explorer Paper A.pdf', 'Phase Ten Explorer Paper B.pdf')"
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
  return fetchJson(`${apiUrl}/library/import?duplicate_strategy=cancel`, { method: 'POST', body });
}

async function createConcept(name) {
  return fetchJson(`${apiUrl}/concepts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      description: `${name} description`,
      category: 'Explorer',
      tags: ['phase10', 'explorer']
    })
  });
}

async function setup() {
  await cleanup();
  const papers = await Promise.all(paperNames.map(importPaper));
  const concepts = await Promise.all(conceptNames.map(createConcept));
  const project = await fetchJson(`${apiUrl}/workspace/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: projectName })
  });
  const brainstorm = await fetchJson(`${apiUrl}/workspace/brainstorm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: brainstormName })
  });
  const review = await fetchJson(`${apiUrl}/literature-reviews`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: reviewName })
  });

  await fetchJson(`${apiUrl}/links/concept:${encodeURIComponent(concepts[0].slug)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_ids: [
        `paper:${papers[0].id}`,
        `paper:${papers[1].id}`,
        `concept:${concepts[1].slug}`,
        project.object.id,
        brainstorm.object.id,
        review.review.id
      ]
    })
  });
}

async function main() {
  await setup();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  try {
    await page.goto(`${frontendUrl}research-explorer`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Explore', exact: true }).waitFor();
    await page.getByPlaceholder('Search everything').fill(conceptNames[0]);
    await page.getByRole('button', { name: new RegExp(conceptNames[0]) }).first().click();
    await page.getByRole('heading', { name: conceptNames[0] }).waitFor();
    await page.getByText(`${conceptNames[0]} description`).waitFor();
    await page.getByText('phase10, explorer').waitFor();

    await page.getByRole('button', { name: 'Phase Ten Explorer Paper A', exact: true }).click();
    await page.getByRole('heading', { name: 'Phase Ten Explorer Paper A' }).waitFor();
    await page.getByRole('button', { name: 'Back' }).click();
    await page.getByRole('heading', { name: conceptNames[0] }).waitFor();
    await page.getByRole('button', { name: 'Forward' }).click();
    await page.getByRole('heading', { name: 'Phase Ten Explorer Paper A' }).waitFor();

    await page.getByRole('button', { name: new RegExp(conceptNames[0]) }).first().click();
    await page.getByRole('heading', { name: conceptNames[0] }).waitFor();
    for (const name of [
      'Phase Ten Explorer Paper B',
      conceptNames[1],
      projectName,
      brainstormName,
      reviewName
    ]) {
      await page.getByRole('button', { name: new RegExp(name) }).first().click();
      await page.getByRole('heading', { name }).waitFor();
      await page.getByRole('button', { name: new RegExp(conceptNames[0]) }).first().click();
      await page.getByRole('heading', { name: conceptNames[0] }).waitFor();
    }

    await page.getByRole('heading', { name: 'Recently Visited' }).waitFor();
    await page.getByText(reviewName).first().waitFor();
    await page.getByText(projectName).first().waitFor();

    console.log('Research Explorer verification passed.');
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
