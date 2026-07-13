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
const testDir = '/tmp/research-os-knowledge-engine-ui';
const pdfPath = path.join(testDir, 'Knowledge Engine Verification.pdf');
const conceptNames = [
  'Phase Five Machine Learning',
  'Phase Five Reinforcement Learning',
  'Phase Five Multi Armed Bandits'
];

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
    (entry) => entry.original_filename === 'Knowledge Engine Verification.pdf'
  )) {
    await fs.rm(item.file_path, { force: true }).catch(() => undefined);
    await fs.rm(item.markdown_path, { force: true }).catch(() => undefined);
  }

  const storage = await fetchJson(`${apiUrl}/storage`).catch(() => null);
  if (storage?.vault_path) {
    for (const name of conceptNames) {
      await fs
        .rm(path.join(storage.vault_path, '03 Knowledge', `${name}.md`), { force: true })
        .catch(() => undefined);
    }
  }

  const db = new DatabaseSync(path.join(rootDir, 'backend', 'research_os.db'));
  db.prepare(
    "delete from library_items where original_filename = 'Knowledge Engine Verification.pdf'"
  ).run();
  db.close();
}

async function createConcept(page, name, category, tags) {
  await page.goto(`${frontendUrl}knowledge`, { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: 'New Concept' }).first().click();
  await page.getByLabel('Name').fill(name);
  await page.getByLabel('Description').fill(`${name} description`);
  await page.getByLabel('Category').fill(category);
  await page.getByLabel('Tags').fill(tags);
  const createResponse = page.waitForResponse(
    (response) => response.url().includes('/api/v1/concepts') && response.request().method() === 'POST'
  );
  await page.getByRole('button', { name: 'Create Concept' }).click();
  const response = await createResponse;
  if (!response.ok()) throw new Error(`Concept creation failed for ${name}: ${response.status()}`);
  await page.getByText(name, { exact: true }).waitFor();
}

async function selectExploreConcept(page, name) {
  await page.getByPlaceholder('Search concepts').fill(name);
  await page.locator('aside').nth(1).getByRole('button').filter({ hasText: name }).first().click();
  await page.getByRole('heading', { name }).waitFor();
}

async function main() {
  await cleanup();
  await createPdf(pdfPath);

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  try {
    await createConcept(page, conceptNames[0], 'Field', 'phase5, systems');
    await createConcept(page, conceptNames[1], 'Field', 'phase5, learning');
    await createConcept(page, conceptNames[2], 'Method', 'phase5, bandits');

    await page.goto(`${frontendUrl}explore`, { waitUntil: 'networkidle' });
    await selectExploreConcept(page, conceptNames[0]);
    await page.getByLabel(conceptNames[1]).check();
    await page.getByRole('button', { name: 'Save Links' }).click();
    await page.getByText('Related concepts saved in Markdown.').waitFor();

    await selectExploreConcept(page, conceptNames[1]);
    await page.getByLabel(conceptNames[2]).check();
    await page.getByRole('button', { name: 'Save Links' }).click();
    await page.getByText('Related concepts saved in Markdown.').waitFor();

    const storage = await fetchJson(`${apiUrl}/storage`);
    const machineLearningPath = path.join(storage.vault_path, '03 Knowledge', `${conceptNames[0]}.md`);
    const reinforcementPath = path.join(storage.vault_path, '03 Knowledge', `${conceptNames[1]}.md`);
    const machineLearningMarkdown = await fs.readFile(machineLearningPath, 'utf8');
    const reinforcementMarkdown = await fs.readFile(reinforcementPath, 'utf8');
    if (!machineLearningMarkdown.includes(`[[${conceptNames[1]}]]`)) {
      throw new Error('First concept relation was not written to Markdown.');
    }
    if (!reinforcementMarkdown.includes(`[[${conceptNames[2]}]]`)) {
      throw new Error('Second concept relation was not written to Markdown.');
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
    await page.getByText('Knowledge Engine Verification.pdf').click();

    await page.getByText('Knowledge Workspace').waitFor();
    await page.getByRole('button', { name: 'Concepts' }).click();
    await page.getByLabel(conceptNames[1]).check();
    await page.getByLabel(conceptNames[2]).check();
    await page.getByRole('button', { name: 'Save Links' }).click();
    await page.getByText('Concept links saved in the Paper Markdown note.').waitFor();

    const importedItem = (await fetchItems()).find(
      (item) => item.original_filename === 'Knowledge Engine Verification.pdf'
    );
    if (!importedItem) throw new Error('Imported paper not found.');
    const paperMarkdown = await fs.readFile(importedItem.markdown_path, 'utf8');
    if (!paperMarkdown.includes(`[[${conceptNames[1]}]]`) || !paperMarkdown.includes(`[[${conceptNames[2]}]]`)) {
      throw new Error('Paper concept links were not written to Markdown.');
    }

    await page.goto(`${frontendUrl}explore`, { waitUntil: 'networkidle' });
    await selectExploreConcept(page, conceptNames[0]);
    await page.getByRole('button', { name: conceptNames[1] }).click();
    await page.getByRole('heading', { name: conceptNames[1] }).waitFor();
    await page.getByRole('button', { name: conceptNames[2] }).click();
    await page.getByRole('heading', { name: conceptNames[2] }).waitFor();
    await page.getByRole('link', { name: 'Knowledge Engine Verification.pdf' }).click();
    await page.getByText('Knowledge Workspace').waitFor();
    await page.getByRole('button', { name: 'Concepts' }).click();
    await page.getByRole('link', { name: conceptNames[2] }).click();
    await page.getByRole('heading', { name: conceptNames[2] }).waitFor();
    await page.getByText('Knowledge Engine Verification.pdf').waitFor();

    console.log('Knowledge Engine verification passed.');
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
