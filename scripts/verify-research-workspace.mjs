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
const sourcePdf = '/tmp/research-os-phase6-real-pdfs/Attention Is All You Need.pdf';
const testPdf = '/tmp/research-os-phase8-workspace/Phase Eight Workspace Paper.pdf';
const paperOriginal = 'Phase Eight Workspace Paper.pdf';
const paperTitle = 'Phase Eight Workspace Paper';
const conceptName = 'Phase Eight Workspace Concept';
const brainstormName = 'Phase Eight Brainstorm';
const projectName = 'Phase Eight Project';

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Request failed ${url}: ${response.status}`);
  return response.json();
}

async function cleanup() {
  const items = (await fetchJson(`${apiUrl}/library`).catch(() => ({ items: [] }))).items;
  for (const item of items.filter((entry) => entry.original_filename === paperOriginal)) {
    await fs.rm(item.file_path, { force: true }).catch(() => undefined);
    await fs.rm(item.markdown_path, { force: true }).catch(() => undefined);
  }

  const storage = await fetchJson(`${apiUrl}/storage`).catch(() => null);
  if (storage?.vault_path) {
    await fs.rm(path.join(storage.vault_path, '03 Knowledge', `${conceptName}.md`), { force: true }).catch(() => undefined);
    await fs.rm(path.join(storage.vault_path, '04 Brainstorm', `${brainstormName}.md`), { force: true }).catch(() => undefined);
    await fs.rm(path.join(storage.vault_path, '01 Projects', `${projectName}.md`), { force: true }).catch(() => undefined);
  }

  const db = new DatabaseSync(path.join(rootDir, 'backend', 'research_os.db'));
  db.prepare("delete from library_items where original_filename = ?").run(paperOriginal);
  db.close();
}

async function preparePdf() {
  await fs.mkdir(path.dirname(testPdf), { recursive: true });
  await fs.copyFile(sourcePdf, testPdf);
}

async function linkResult(page, query, label) {
  await page.getByPlaceholder('Search papers, concepts, projects, brainstorm notes, reviews').fill(query);
  await page.locator('label').filter({ hasText: label }).first().getByRole('checkbox').check();
  await page.getByRole('button', { name: 'Link', exact: true }).click();
  await page.getByText('Links saved in Markdown.').waitFor();
}

async function main() {
  await preparePdf();
  await cleanup();

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  try {
    await page.goto(frontendUrl, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Continue your research' }).waitFor();
    await page.getByText('Quick Actions').waitFor();

    await page.getByRole('link', { name: 'Import PDF' }).click();
    await page.getByRole('heading', { name: 'Drop PDF Here' }).waitFor();
    const chooserPromise = page.waitForEvent('filechooser');
    await page.getByTestId('pdf-file-input').click();
    const chooser = await chooserPromise;
    await chooser.setFiles(testPdf);
    await page.getByText('PDF Metadata Preview').waitFor();
    await page.getByLabel('Title').fill(paperTitle);
    await page.getByRole('button', { name: 'Import', exact: true }).click();
    await page.getByText('Paper imported successfully').waitFor();
    await page.getByText(paperTitle).first().click();
    await page.getByText('Knowledge Workspace').waitFor();

    await page.goto(`${frontendUrl}knowledge`, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'New Concept' }).first().click();
    await page.getByLabel('Name').fill(conceptName);
    await page.getByLabel('Description').fill('Workspace validation concept');
    await page.getByLabel('Category').fill('Workspace');
    await page.getByLabel('Tags').fill('phase8, workspace');
    await page.getByRole('button', { name: 'Create Concept' }).click();
    await page.getByText(conceptName, { exact: true }).waitFor();

    await page.goto(frontendUrl, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'New Brainstorm' }).click();
    await page.getByLabel('Brainstorm Title').fill(brainstormName);
    await page.getByRole('button', { name: 'Create' }).click();
    await page.getByRole('heading', { name: brainstormName }).waitFor();

    await page.goto(frontendUrl, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'New Project' }).click();
    await page.getByLabel('Project Title').fill(projectName);
    await page.getByRole('button', { name: 'Create' }).click();
    await page.getByRole('heading', { name: projectName }).first().waitFor();

    const item = (await fetchJson(`${apiUrl}/library`)).items.find(
      (entry) => entry.original_filename === paperOriginal
    );
    if (!item) throw new Error('Imported paper missing from API.');

    await page.goto(`${frontendUrl}knowledge/${item.id}`, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'Relations' }).click();
    await linkResult(page, conceptName, conceptName);
    await linkResult(page, brainstormName, brainstormName);
    await linkResult(page, projectName, projectName);

    await page.goto(`${frontendUrl}brainstorm?selected=brainstorm:${encodeURIComponent(brainstormName)}`, { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'Relations' }).click();
    await linkResult(page, conceptName, conceptName);

    await page.goto(frontendUrl, { waitUntil: 'networkidle' });
    await page.getByText(paperTitle).first().waitFor();
    await page.getByText(conceptName).first().waitFor();
    await page.getByText(brainstormName).first().waitFor();
    await page.getByPlaceholder('Search papers, concepts, projects, brainstorm, reviews').first().fill(conceptName);
    await page.getByText(conceptName).first().waitFor();

    const paperMarkdown = await fs.readFile(item.markdown_path, 'utf8');
    const storage = await fetchJson(`${apiUrl}/storage`);
    const brainstormMarkdown = await fs.readFile(
      path.join(storage.vault_path, '04 Brainstorm', `${brainstormName}.md`),
      'utf8'
    );

    if (!paperMarkdown.includes(`[[${conceptName}]]`)) throw new Error('Paper to Concept link missing.');
    if (!paperMarkdown.includes(`[[${brainstormName}]]`)) throw new Error('Paper to Brainstorm link missing.');
    if (!paperMarkdown.includes(`[[${projectName}]]`)) throw new Error('Paper to Project link missing.');
    if (!brainstormMarkdown.includes(`[[${conceptName}]]`)) throw new Error('Brainstorm to Concept link missing.');

    console.log('Research Workspace verification passed.');
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
