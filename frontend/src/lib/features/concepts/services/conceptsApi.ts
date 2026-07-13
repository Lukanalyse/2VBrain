import { API_BASE_URL } from '$lib/config/api';
import type {
  Concept,
  ConceptCreate,
  ConceptDetail,
  ConceptListResponse,
  PaperConceptLinks
} from '$lib/features/concepts/types/concept';

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
    throw new Error(payload?.detail ?? 'Concept request failed.');
  }

  return response.json() as Promise<T>;
}

export async function listConcepts(): Promise<Concept[]> {
  const data = await request<ConceptListResponse>('/concepts');
  return data.concepts;
}

export function createConcept(payload: ConceptCreate): Promise<Concept> {
  return request<Concept>('/concepts', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function getConcept(slug: string): Promise<ConceptDetail> {
  return request<ConceptDetail>(`/concepts/${encodeURIComponent(slug)}`);
}

export function getPaperConceptLinks(
  itemId: number
): Promise<PaperConceptLinks> {
  return request<PaperConceptLinks>(`/reader/items/${itemId}/concepts`);
}

export function savePaperConceptLinks(
  itemId: number,
  conceptNames: string[]
): Promise<PaperConceptLinks> {
  return request<PaperConceptLinks>(`/reader/items/${itemId}/concepts`, {
    method: 'PUT',
    body: JSON.stringify({ concept_names: conceptNames })
  });
}
