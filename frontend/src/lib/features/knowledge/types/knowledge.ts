export type KnowledgeTab =
  'notes' | 'metadata' | 'concepts' | 'relations' | 'references' | 'ai';

export type KnowledgeItem = {
  id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  markdown_path: string;
  imported_at: string;
  status: string;
  title: string | null;
  authors: string | null;
  journal: string | null;
  conference: string | null;
  year: number | null;
  doi: string | null;
  abstract: string | null;
  keywords: string | null;
};

export type MarkdownDocument = {
  library_item_id: number;
  markdown_path: string;
  content: string;
};

export type SaveState = 'saved' | 'unsaved' | 'saving' | 'error';
