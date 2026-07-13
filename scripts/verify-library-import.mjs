import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { DatabaseSync } from 'node:sqlite';
import { createRequire } from 'node:module';

const rootDir = process.cwd();
const require = createRequire(path.join(rootDir, 'frontend', 'package.json'));
const { chromium } = require('@playwright/test');
const frontendUrl = 'http://127.0.0.1:5173/';
const apiUrl = 'http://127.0.0.1:8000/api/v1';
const testDir = '/tmp/research-os-library-ui';
const clickPdf = path.join(testDir, 'Attention Is All You Need.pdf');
const dropPdf = path.join(testDir, 'Drop Import Verification.pdf');

async function createPdf(filePath) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, Buffer.from('%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n'));
}

async function cleanup(items) {
  for (const item of items) {
    await fs.rm(item.file_path, { force: true }).catch(() => undefined);
    await fs.rm(item.markdown_path, { force: true }).catch(() => undefined);
  }

  const db = new DatabaseSync(path.join(rootDir, 'backend', 'research_os.db'));
  db.prepare(
    "delete from library_items where original_filename in ('Attention Is All You Need.pdf', 'Drop Import Verification.pdf')"
  ).run();
  db.close();
}

async function fetchItems() {
  const response = await fetch(`${apiUrl}/library`);
  if (!response.ok) throw new Error(`Unable to fetch library items: ${response.status}`);
  return (await response.json()).items;
}

async function main() {
  await createPdf(clickPdf);
  await createPdf(dropPdf);

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  try {
    await page.goto(frontendUrl, { waitUntil: 'networkidle' });
    await page.getByRole('link', { name: 'Library' }).click();
    await page.getByRole('heading', { name: 'Drop PDF Here' }).waitFor();

    const chooserPromise = page.waitForEvent('filechooser');
    await page.getByTestId('pdf-file-input').click();
    const chooser = await chooserPromise;
    await chooser.setFiles(clickPdf);
    await page.getByText('PDF Metadata Preview').waitFor();
    await page.getByRole('button', { name: 'Import', exact: true }).click();

    await page.getByRole('heading', { name: 'Importing paper...' }).waitFor();
    await page.getByText('Paper imported successfully').waitFor();
    await page.getByText('Attention Is All You Need.pdf').waitFor();
    await page.getByText('Unread').first().waitFor();
    await page.getByText('Imported just now').first().waitFor();

    const itemsAfterClick = await fetchItems();
    const clickItem = itemsAfterClick.find(
      (item) => item.original_filename === 'Attention Is All You Need.pdf'
    );
    if (!clickItem) throw new Error('Click import did not create a library item.');
    await fs.access(clickItem.file_path);
    await fs.access(clickItem.markdown_path);

    const duplicateChooserPromise = page.waitForEvent('filechooser');
    await page.getByTestId('pdf-file-input').click();
    const duplicateChooser = await duplicateChooserPromise;
    await duplicateChooser.setFiles(clickPdf);
    await page.getByText('PDF Metadata Preview').waitFor();
    await page.getByRole('button', { name: 'Import', exact: true }).click();
    await page.getByRole('heading', { name: 'Already imported' }).waitFor();
    await page.getByRole('button', { name: 'Keep both' }).click();
    await page.getByText('Attention Is All You Need 2.pdf').waitFor();

    const dropZone = page.getByTestId('pdf-dropzone');
    await dropZone.dispatchEvent('dragenter', {
      dataTransfer: await page.evaluateHandle(() => new DataTransfer())
    });
    await page.getByRole('heading', { name: 'Drop to import' }).waitFor();

    const dataTransfer = await page.evaluateHandle(async ({ name, type, buffer }) => {
      const data = Uint8Array.from(buffer);
      const file = new File([data], name, { type });
      const transfer = new DataTransfer();
      transfer.items.add(file);
      return transfer;
    }, {
      name: 'Drop Import Verification.pdf',
      type: 'application/pdf',
      buffer: Array.from(await fs.readFile(dropPdf))
    });

    await dropZone.dispatchEvent('drop', { dataTransfer });
    await page.getByText('PDF Metadata Preview').waitFor();
    await page.getByRole('button', { name: 'Import', exact: true }).click();
    await page.getByText('Drop Import Verification.pdf').waitFor();

    const finalItems = await fetchItems();
    const importedTestItems = finalItems.filter((item) =>
      ['Attention Is All You Need.pdf', 'Drop Import Verification.pdf'].includes(
        item.original_filename
      )
    );
    if (importedTestItems.length < 3) {
      throw new Error(`Expected 3 test imports, found ${importedTestItems.length}.`);
    }

    await cleanup(importedTestItems);
    console.log('Library UI import verification passed.');
  } finally {
    await browser.close();
  }
}

main().catch(async (error) => {
  console.error(error);
  const items = await fetchItems().catch(() => []);
  await cleanup(
    items.filter((item) =>
      ['Attention Is All You Need.pdf', 'Drop Import Verification.pdf'].includes(
        item.original_filename
      )
    )
  ).catch(() => undefined);
  process.exit(1);
});
