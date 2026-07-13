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
const testDir = '/tmp/research-os-phase12-workspace';
const testPdf = path.join(testDir, 'Phase Twelve Workspace Paper.pdf');
const paperOriginal = 'Phase Twelve Workspace Paper.pdf';
const paperTitle = 'Phase Twelve Workspace Paper';
const conceptName = 'Phase Twelve Workspace Concept';
const projectName = 'Phase Twelve Workspace Project';
const noteText = 'Phase 12 autosaved workspace note.';

async function fetchJson(url, init) {
  const response = await fetch(url, init);
  if (!response.ok) throw new Error(`Request failed ${url}: ${response.status} ${await response.text()}`);
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
    await fs.rm(path.join(storage.vault_path, '01 Projects', `${projectName}.md`), { force: true }).catch(() => undefined);
  }

  const db = new DatabaseSync(path.join(rootDir, 'backend', 'research_os.db'));
  db.prepare('delete from library_items where original_filename = ?').run(paperOriginal);
  db.close();
}

async function setupFixtures() {
  await cleanup();
  await fs.mkdir(testDir, { recursive: true });
  await fs.copyFile(sourcePdf, testPdf);
  await fetchJson(`${apiUrl}/concepts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: conceptName,
      description: 'Workspace concept for Phase 12 validation',
      category: 'Workspace',
      tags: ['phase12']
    })
  });
  await fetchJson(`${apiUrl}/workspace/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: projectName })
  });
}

async function openFromWorkspaceSearch(page, name) {
  await page.getByPlaceholder('Open paper, concept, project...').fill(name);
  await page.getByRole('button', { name: new RegExp(name) }).first().click();
  await page.getByRole('button', { name: new RegExp(name) }).first().waitFor();
}

async function main() {
  await setupFixtures();

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  try {
    await page.goto(frontendUrl, { waitUntil: 'networkidle' });
    await page.evaluate(() => {
      localStorage.removeItem('research-os.workspace.tabs');
      localStorage.removeItem('research-os.workspace.recent');
    });

    await page.goto(`${frontendUrl}library`, { waitUntil: 'networkidle' });
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

    await page.locator('h1').filter({ hasText: 'Workspace' }).waitFor();
    await page.getByText(paperTitle).first().waitFor();

    const paperTextarea = page.locator('textarea').first();
    const currentPaperContent = await paperTextarea.inputValue();
    const saveResponse = page.waitForResponse(
      (response) =>
        response.url().includes('/api/v1/workspace/objects/paper%3A') &&
        response.request().method() === 'PUT'
    );
    await paperTextarea.fill(`${currentPaperContent}\n${noteText}\n`);
    const response = await saveResponse;
    if (!response.ok()) throw new Error(`Workspace paper save failed: ${response.status()}`);
    await page.getByText('● Saved').waitFor();

    await openFromWorkspaceSearch(page, conceptName);
    await page.getByText(conceptName).first().waitFor();
    await page.getByRole('button', { name: new RegExp(paperTitle) }).first().click();
    if (!(await page.locator('textarea').first().inputValue()).includes(noteText)) {
      throw new Error('Paper note was not preserved when switching tabs.');
    }

    await openFromWorkspaceSearch(page, projectName);
    await page.getByRole('button', { name: new RegExp(paperTitle) }).first().waitFor();
    await page.getByRole('button', { name: new RegExp(conceptName) }).first().waitFor();
    await page.getByRole('button', { name: new RegExp(projectName) }).first().waitFor();

    await page.reload({ waitUntil: 'networkidle' });
    await page.locator('h1').filter({ hasText: 'Workspace' }).waitFor();
    await page.getByRole('button', { name: new RegExp(paperTitle) }).first().click();
    if (!(await page.locator('textarea').first().inputValue()).includes(noteText)) {
      throw new Error('Paper note was not restored after reload.');
    }
    await page.getByRole('button', { name: new RegExp(conceptName) }).first().waitFor();
    await page.getByRole('button', { name: new RegExp(projectName) }).first().waitFor();

    const item = (await fetchJson(`${apiUrl}/library`)).items.find(
      (entry) => entry.original_filename === paperOriginal
    );
    if (!item) throw new Error('Imported workspace paper missing.');
    const markdown = await fs.readFile(item.markdown_path, 'utf8');
    if (!markdown.includes(noteText)) throw new Error('Autosaved note was not written to the Vault.');

    console.log('Research Workspace core verification passed.');
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
