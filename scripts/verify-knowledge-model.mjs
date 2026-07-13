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
const testDir = '/tmp/research-os-knowledge-model-ui';
const pdfPath = path.join(testDir, 'Knowledge Model Verification.pdf');
const conceptName = 'Phase Four Concept Verification';
const conceptSlug = conceptName;

async function createPdf(filePath) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, Buffer.from('%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n'));
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Request failed ${url}: ${response.status}`);
  return response.json();
}

async function fetchItems() {
  return (await fetchJson(`${apiUrl}/library`)).items;
}

async function cleanup() {
  const items = await fetchItems().catch(() => []);
  for (const item of items.filter(
    (entry) => entry.original_filename === 'Knowledge Model Verification.pdf'
  )) {
    await fs.rm(item.file_path, { force: true }).catch(() => undefined);
    await fs.rm(item.markdown_path, { force: true }).catch(() => undefined);
  }

  const storage = await fetchJson(`${apiUrl}/storage`).catch(() => null);
  if (storage?.vault_path) {
    await fs
      .rm(path.join(storage.vault_path, '03 Knowledge', `${conceptName}.md`), { force: true })
      .catch(() => undefined);
  }

  const db = new DatabaseSync(path.join(rootDir, 'backend', 'research_os.db'));
  db.prepare(
    "delete from library_items where original_filename = 'Knowledge Model Verification.pdf'"
  ).run();
  db.close();
}

async function main() {
  await cleanup();
  await createPdf(pdfPath);

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  try {
    await page.goto(`${frontendUrl}knowledge`, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Knowledge' }).waitFor();
    await page.getByRole('button', { name: 'New Concept' }).first().click();
    await page.getByLabel('Name').fill(conceptName);
    await page.getByLabel('Description').fill('Concept created by the Phase 4 verification.');
    await page.getByLabel('Category').fill('Method');
    await page.getByLabel('Tags').fill('phase4, verification');
    await page.getByRole('button', { name: 'Create Concept' }).click();
    await page.getByText(conceptName).waitFor();

    const conceptDetail = await fetchJson(`${apiUrl}/concepts/${encodeURIComponent(conceptSlug)}`);
    await fs.access(conceptDetail.concept.markdown_path);
    const conceptMarkdown = await fs.readFile(conceptDetail.concept.markdown_path, 'utf8');
    if (!conceptMarkdown.includes('type: concept') || !conceptMarkdown.includes('# Related Papers')) {
      throw new Error('Concept Markdown template was not created correctly.');
    }
    if (!conceptDetail.concept.markdown_path.includes('03 Knowledge')) {
      throw new Error('Concept was not created in 03 Knowledge.');
    }

    await page.getByRole('link', { name: 'Library' }).click();
    await page.getByRole('heading', { name: 'Drop PDF Here' }).waitFor();
    const chooserPromise = page.waitForEvent('filechooser');
    await page.getByTestId('pdf-file-input').click();
    const chooser = await chooserPromise;
    await chooser.setFiles(pdfPath);
    await page.getByText('PDF Metadata Preview').waitFor();
    await page.getByRole('button', { name: 'Import', exact: true }).click();
    await page.getByText('Paper imported successfully').waitFor();
    await page.getByText('Knowledge Model Verification.pdf').click();

    await page.getByText('Knowledge Workspace').waitFor();
    await page.getByRole('button', { name: 'Concepts' }).click();
    await page.getByText('Link Concept').waitFor();
    await page.getByText(conceptName).waitFor();
    await page.getByLabel(conceptName).check();
    await page.getByRole('button', { name: 'Save Links' }).click();
    await page.getByText('Concept links saved in the Paper Markdown note.').waitFor();

    const items = await fetchItems();
    const importedItem = items.find(
      (item) => item.original_filename === 'Knowledge Model Verification.pdf'
    );
    if (!importedItem) throw new Error('Imported paper was not found.');

    const paperMarkdown = await fs.readFile(importedItem.markdown_path, 'utf8');
    if (!paperMarkdown.includes(`[[${conceptName}]]`)) {
      throw new Error('Concept link was not written to the Paper Markdown note.');
    }

    await page.goto(`${frontendUrl}knowledge/concepts/${encodeURIComponent(conceptSlug)}`, {
      waitUntil: 'networkidle'
    });
    await page.getByRole('heading', { name: conceptName }).waitFor();
    await page.getByText('References').waitFor();
    await page.getByText('Knowledge Model Verification.pdf').waitFor();

    console.log('Knowledge Model verification passed.');
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
