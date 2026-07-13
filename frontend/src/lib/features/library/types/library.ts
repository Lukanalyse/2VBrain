export type LibraryItem = {
  id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  markdown_path: string;
  imported_at: string;
  status: string;
  collection_status: 'inbox' | 'workspace' | 'library';
  project_id: string | null;
  title: string | null;
  authors: string | null;
  journal: string | null;
  conference: string | null;
  year: number | null;
  doi: string | null;
  abstract: string | null;
  keywords: string | null;
  publisher: string | null;
  source_url: string | null;
  metadata_source: string | null;
  metadata_confidence: string | null;
  metadata_updated_at: string | null;
  reading_progress: number;
  importance: string | null;
  priority: string | null;
  domain: string | null;
  method: string | null;
  difficulty: string | null;
  personal_tags: string | null;
};

export type LibraryListResponse = {
  items: LibraryItem[];
};

export type LibraryImportConflict = {
  reason: 'already_imported';
  message: string;
  existing_item: LibraryItem;
};

export type DuplicateStrategy = 'cancel' | 'replace' | 'keep_both';

export type PdfMetadataPreview = {
  title: string;
  authors: string;
  journal: string;
  conference: string;
  year: number | null;
  doi: string;
  abstract: string;
  keywords: string;
  publisher: string;
  source_url: string;
  metadata_source: string;
  metadata_confidence: string;
  reading_status: string;
  reading_progress: number;
  importance: string;
  priority: string;
  domain: string;
  method: string;
  difficulty: string;
  personal_tags: string;
  project_id: string;
};
