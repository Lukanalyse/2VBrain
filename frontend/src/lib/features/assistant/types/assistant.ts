import type { LinkableObject } from '$lib/features/linking/types/linking';

export type AssistantConfig = {
  provider: 'ollama';
  base_url: string;
  chat_model: string;
  embedding_model: string;
  context_length: number;
  local_only: boolean;
};

export type AssistantModelInfo = {
  name: string;
  size: number | null;
  parameter_size: string | null;
  quantization_level: string | null;
};

export type AssistantStatus = {
  available: boolean;
  config: AssistantConfig;
  models: AssistantModelInfo[];
  error: string | null;
};

export type ProjectIndexStatus = {
  project_id: string;
  ready: boolean;
  document_count: number;
  chunk_count: number;
  embedding_model: string;
  updated_documents: number;
  errors: string[];
};

export type AssistantHistoryMessage = {
  role: 'user' | 'assistant';
  content: string;
};

export type AssistantCitation = {
  label: string;
  object: LinkableObject;
  source_kind: 'markdown' | 'pdf';
  source_title: string;
  heading: string;
  page_number: number | null;
  excerpt: string;
};

export type ProjectAssistantResponse = {
  answer: string;
  citations: AssistantCitation[];
  insufficient_evidence: boolean;
};
