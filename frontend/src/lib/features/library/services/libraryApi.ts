import { API_BASE_URL } from '$lib/config/api';
import type {
  DuplicateStrategy,
  LibraryImportConflict,
  LibraryItem,
  LibraryListResponse,
  PdfMetadataPreview
} from '$lib/features/library/types/library';

export class LibraryConflictError extends Error {
  conflict: LibraryImportConflict;
  file: File;

  constructor(conflict: LibraryImportConflict, file: File) {
    super(conflict.message);
    this.conflict = conflict;
    this.file = file;
  }
}

export async function listLibraryItems(): Promise<LibraryItem[]> {
  const response = await fetch(`${API_BASE_URL}/library`);

  if (!response.ok) {
    throw new Error('Unable to load the Research Library.');
  }

  const data = (await response.json()) as LibraryListResponse;
  return data.items;
}

export async function importPdf(
  file: File,
  duplicateStrategy: DuplicateStrategy = 'cancel',
  metadata: PdfMetadataPreview
): Promise<LibraryItem> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', metadata.title);
  formData.append('authors', metadata.authors);
  formData.append('journal', metadata.journal);
  formData.append('conference', metadata.conference);
  if (metadata.year !== null) formData.append('year', String(metadata.year));
  formData.append('doi', metadata.doi);
  formData.append('abstract', metadata.abstract);
  formData.append('keywords', metadata.keywords);
  formData.append('publisher', metadata.publisher);
  formData.append('source_url', metadata.source_url);
  formData.append('metadata_source', metadata.metadata_source);
  formData.append('metadata_confidence', metadata.metadata_confidence);
  formData.append('reading_status', metadata.reading_status);
  formData.append('reading_progress', String(metadata.reading_progress));
  formData.append('importance', metadata.importance);
  formData.append('priority', metadata.priority);
  formData.append('domain', metadata.domain);
  formData.append('method', metadata.method);
  formData.append('difficulty', metadata.difficulty);
  formData.append('personal_tags', metadata.personal_tags);
  formData.append('project_id', metadata.project_id);

  const response = await fetch(
    `${API_BASE_URL}/library/import?duplicate_strategy=${duplicateStrategy}`,
    {
      method: 'POST',
      body: formData
    }
  );

  if (response.status === 409) {
    const payload = (await response.json()) as {
      detail: LibraryImportConflict;
    };
    throw new LibraryConflictError(payload.detail, file);
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(payload?.detail ?? 'Unable to import this PDF.');
  }

  return response.json() as Promise<LibraryItem>;
}

export async function previewPdfMetadata(
  file: File
): Promise<PdfMetadataPreview> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/library/preview`, {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(payload?.detail ?? 'Unable to preview PDF metadata.');
  }

  return response.json() as Promise<PdfMetadataPreview>;
}
