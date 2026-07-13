import { API_BASE_URL } from '$lib/config/api';
import type {
  KnowledgeItem,
  MarkdownDocument
} from '$lib/features/knowledge/types/knowledge';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers
    },
    ...init
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(payload?.detail ?? 'Knowledge workspace request failed.');
  }

  return response.json() as Promise<T>;
}

export function getKnowledgeItem(itemId: number): Promise<KnowledgeItem> {
  return request<KnowledgeItem>(`/reader/items/${itemId}`);
}

export function getMarkdownDocument(itemId: number): Promise<MarkdownDocument> {
  return request<MarkdownDocument>(`/reader/items/${itemId}/markdown`);
}

export function saveMarkdownDocument(
  itemId: number,
  content: string
): Promise<MarkdownDocument> {
  return request<MarkdownDocument>(`/reader/items/${itemId}/markdown`, {
    method: 'PUT',
    body: JSON.stringify({ content })
  });
}

export function openPdf(itemId: number): Promise<{ status: string }> {
  return request<{ status: string }>(`/reader/items/${itemId}/open-pdf`, {
    method: 'POST'
  });
}
