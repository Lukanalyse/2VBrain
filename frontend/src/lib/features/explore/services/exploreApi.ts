import { API_BASE_URL } from '$lib/config/api';
import type {
  ConceptConceptLinksResponse,
  ExploreListResponse,
  KnowledgeConceptSummary,
  KnowledgeConceptView
} from '$lib/features/explore/types/explore';

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
    throw new Error(payload?.detail ?? 'Explore request failed.');
  }

  return response.json() as Promise<T>;
}

export async function listExploreConcepts(): Promise<
  KnowledgeConceptSummary[]
> {
  const data = await request<ExploreListResponse>('/explore/concepts');
  return data.concepts;
}

export function getExploreConcept(slug: string): Promise<KnowledgeConceptView> {
  return request<KnowledgeConceptView>(
    `/explore/concepts/${encodeURIComponent(slug)}`
  );
}

export function saveRelatedConcepts(
  slug: string,
  conceptNames: string[]
): Promise<ConceptConceptLinksResponse> {
  return request<ConceptConceptLinksResponse>(
    `/explore/concepts/${encodeURIComponent(slug)}/concepts`,
    {
      method: 'PUT',
      body: JSON.stringify({ concept_names: conceptNames })
    }
  );
}
