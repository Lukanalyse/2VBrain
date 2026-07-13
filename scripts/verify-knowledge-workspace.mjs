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
const testDir = '/tmp/research-os-knowledge-ui';
const pdfPath = path.join(testDir, 'Knowledge Workspace Verification.pdf');
const noteMarker = 'Knowledge workspace note persisted by UI test.';

async function createPdf(filePath) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, Buffer.from('%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n'));
}

async function fetchItems() {
  const response = await fetch(`${apiUrl}/library`);
  if (!response.ok) throw new Error(`Unable to fetch library items: ${response.status}`);
  return (await response.json()).items;
}

async function cleanup(items) {
  for (const item of items) {
    await fs.rm(item.file_path, { force: true }).catch(() => undefined);
    await fs.rm(item.markdown_path, { force: true }).catch(() => undefined);
  }

  const db = new DatabaseSync(path.join(rootDir, 'backend', 'research_os.db'));
  db.prepare(
    "delete from library_items where original_filename = 'Knowledge Workspace Verification.pdf'"
  ).run();
  db.close();
}

async function main() {
  await createPdf(pdfPath);

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  try {
    await page.goto(frontendUrl, { waitUntil: 'networkidle' });
    await page.getByRole('link', { name: 'Library' }).click();
    await page.getByRole('heading', { name: 'Drop PDF Here' }).waitFor();

    const chooserPromise = page.waitForEvent('filechooser');
    await page.getByTestId('pdf-file-input').click();
    const chooser = await chooserPromise;
    await chooser.setFiles(pdfPath);
    await page.getByText('PDF Metadata Preview').waitFor();
    await page.getByRole('button', { name: 'Import', exact: true }).click();

    await page.getByText('Paper imported successfully').waitFor();
    await page.getByText('Knowledge Workspace Verification.pdf').waitFor();
    await page.getByText('Knowledge Workspace Verification.pdf').click();

    await page.getByText('Knowledge Workspace').waitFor();
    await page.getByText('Document', { exact: true }).waitFor();
    await page.getByText('PDF path').waitFor();
    await page.getByRole('button', { name: 'Open PDF' }).waitFor();
    await page.getByRole('button', { name: 'Metadata' }).click();
    await page.getByText('Markdown path').waitFor();
    await page.getByText('Authors').waitFor();
    await page.getByText('DOI').waitFor();
    await page.getByRole('button', { name: 'Concepts' }).click();
    await page.getByText('No concepts linked yet.').waitFor();
    await page.getByRole('button', { name: 'References' }).click();
    await page.getByText('Coming Soon').waitFor();
    await page.getByRole('button', { name: 'AI' }).click();
    await page.getByText('Connect a Local LLM or API provider').waitFor();
    await page.getByRole('button', { name: 'Notes' }).click();

    const textarea = page.locator('textarea');
    await textarea.waitFor();
    const initialContent = await textarea.inputValue();
    if (!initialContent.includes('# Summary') || !initialContent.includes('# Notes')) {
      throw new Error('Markdown note was not loaded automatically.');
    }

    const updatedContent = `${initialContent.trim()}\n\n${noteMarker}\n`;
    await textarea.fill(updatedContent);
    await page.getByText('Unsaved changes', { exact: true }).waitFor();
    await page.getByText('Saved', { exact: true }).waitFor({ timeout: 10000 });

    const items = await fetchItems();
    const importedItem = items.find(
      (item) => item.original_filename === 'Knowledge Workspace Verification.pdf'
    );
    if (!importedItem) throw new Error('Imported item not found after editing.');

    const fileContent = await fs.readFile(importedItem.markdown_path, 'utf8');
    if (!fileContent.includes(noteMarker)) {
      throw new Error('Markdown file in the Vault was not updated.');
    }

    await page.goto(`${frontendUrl}knowledge/${importedItem.id}`, { waitUntil: 'networkidle' });
    await textarea.waitFor();
    const reloadedContent = await textarea.inputValue();
    if (!reloadedContent.includes(noteMarker)) {
      throw new Error('Markdown edits were not preserved after reopening.');
    }

    await cleanup([importedItem]);
    console.log('Knowledge Workspace verification passed.');
  } finally {
    await browser.close();
  }
}

main().catch(async (error) => {
  console.error(error);
  const items = await fetchItems().catch(() => []);
  await cleanup(
    items.filter((item) => item.original_filename === 'Knowledge Workspace Verification.pdf')
  ).catch(() => undefined);
  process.exit(1);
});
