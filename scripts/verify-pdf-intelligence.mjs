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
const pdfDir = '/tmp/research-os-phase6-real-pdfs';

const papers = [
  {
    filename: 'Attention Is All You Need.pdf',
    expectedTitle: 'Attention Is All You Need',
    expectedAuthor: 'Ashish Vaswani',
    expectedAbstract: 'The dominant sequence transduction models',
    correctedYear: '2017',
    correctedConference: 'NeurIPS'
  },
  {
    filename: 'BERT Pre-training of Deep Bidirectional Transformers.pdf',
    expectedTitle: 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
    expectedAuthor: 'Jacob Devlin',
    expectedAbstract: 'We introduce a new language'
  },
  {
    filename: 'Adam A Method for Stochastic Optimization.pdf',
    expectedTitle: 'Adam: A Method for Stochastic Optimization',
    expectedAuthor: 'Diederik P. Kingma',
    expectedAbstract: ''
  }
];

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Request failed ${url}: ${response.status}`);
  return response.json();
}

async function fetchItems() {
  return (await fetchJson(`${apiUrl}/library`)).items;
}

async function cleanup() {
  const originals = papers.map((paper) => paper.filename);
  const items = await fetchItems().catch(() => []);

  for (const item of items.filter((entry) => originals.includes(entry.original_filename))) {
    await fs.rm(item.file_path, { force: true }).catch(() => undefined);
    await fs.rm(item.markdown_path, { force: true }).catch(() => undefined);
  }

  const placeholders = originals.map(() => '?').join(', ');
  const db = new DatabaseSync(path.join(rootDir, 'backend', 'research_os.db'));
  db.prepare(`delete from library_items where original_filename in (${placeholders})`).run(...originals);
  db.close();
}

async function selectPdf(page, pdfPath) {
  const chooserPromise = page.waitForEvent('filechooser');
  await page.getByTestId('pdf-file-input').click();
  const chooser = await chooserPromise;
  await chooser.setFiles(pdfPath);
}

async function dropPdf(page, pdfPath) {
  const dropZone = page.getByTestId('pdf-dropzone');
  await dropZone.dispatchEvent('dragenter', {
    dataTransfer: await page.evaluateHandle(() => new DataTransfer())
  });
  await page.getByRole('heading', { name: 'Drop to import' }).waitFor();

  const dataTransfer = await page.evaluateHandle(async ({ name, buffer }) => {
    const data = Uint8Array.from(buffer);
    const file = new File([data], name, { type: 'application/pdf' });
    const transfer = new DataTransfer();
    transfer.items.add(file);
    return transfer;
  }, {
    name: path.basename(pdfPath),
    buffer: Array.from(await fs.readFile(pdfPath))
  });

  await dropZone.dispatchEvent('drop', { dataTransfer });
}

async function verifyPreview(page, paper) {
  await page.getByText('PDF Metadata Preview').waitFor();

  const title = await page.getByLabel('Title').inputValue();
  const authors = await page.getByLabel('Authors').inputValue();
  const abstract = await page.getByLabel('Abstract').inputValue();

  if (!title.includes(paper.expectedTitle)) {
    throw new Error(`Expected extracted title "${paper.expectedTitle}", got "${title}".`);
  }

  if (paper.expectedAuthor && !authors.includes(paper.expectedAuthor)) {
    throw new Error(`Expected extracted author "${paper.expectedAuthor}", got "${authors}".`);
  }

  if (paper.expectedAbstract && !abstract.includes(paper.expectedAbstract)) {
    throw new Error(`Expected extracted abstract text "${paper.expectedAbstract}".`);
  }

  if (paper.correctedYear) {
    await page.getByLabel('Year').fill(paper.correctedYear);
  }

  if (paper.correctedConference) {
    await page.getByLabel('Conference').fill(paper.correctedConference);
  }
}

async function importPaper(page, paper, mode) {
  const pdfPath = path.join(pdfDir, paper.filename);
  await fs.access(pdfPath);

  if (mode === 'drop') {
    await dropPdf(page, pdfPath);
  } else {
    await selectPdf(page, pdfPath);
  }

  await verifyPreview(page, paper);
  await page.getByRole('button', { name: 'Import', exact: true }).click();
  await page.getByText('Paper imported successfully').waitFor();
  await page.getByText(paper.expectedTitle).first().waitFor();
}

async function verifyImportedFiles() {
  const items = await fetchItems();

  for (const paper of papers) {
    const item = items.find((entry) => entry.original_filename === paper.filename);
    if (!item) throw new Error(`Missing imported item for ${paper.filename}.`);

    if (!item.title?.includes(paper.expectedTitle)) {
      throw new Error(`SQLite/API title not persisted for ${paper.filename}.`);
    }

    if (paper.expectedAuthor && !item.authors?.includes(paper.expectedAuthor)) {
      throw new Error(`SQLite/API authors not persisted for ${paper.filename}.`);
    }

    if (paper.expectedAbstract && !item.abstract?.includes(paper.expectedAbstract)) {
      throw new Error(`SQLite/API abstract not persisted for ${paper.filename}.`);
    }

    if (paper.correctedYear && String(item.year) !== paper.correctedYear) {
      throw new Error(`Corrected year not persisted for ${paper.filename}.`);
    }

    if (paper.correctedConference && item.conference !== paper.correctedConference) {
      throw new Error(`Corrected conference not persisted for ${paper.filename}.`);
    }

    await fs.access(item.file_path);
    await fs.access(item.markdown_path);

    const markdown = await fs.readFile(item.markdown_path, 'utf8');
    if (!markdown.includes(`title: ${JSON.stringify(item.title)}`)) {
      throw new Error(`Markdown title missing for ${paper.filename}.`);
    }
    if (!markdown.includes('# Abstract') || !markdown.includes('# Notes')) {
      throw new Error(`Markdown template incomplete for ${paper.filename}.`);
    }
    if (paper.expectedAbstract && !markdown.includes(paper.expectedAbstract)) {
      throw new Error(`Markdown abstract missing for ${paper.filename}.`);
    }
  }
}

async function main() {
  await cleanup();

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

  try {
    await page.goto(frontendUrl, { waitUntil: 'networkidle' });
    await page.getByRole('link', { name: 'Library' }).click();
    await page.getByRole('heading', { name: 'Drop PDF Here' }).waitFor();

    await importPaper(page, papers[0], 'click');
    await importPaper(page, papers[1], 'drop');
    await importPaper(page, papers[2], 'click');
    await verifyImportedFiles();

    console.log('PDF Intelligence verification passed.');
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
