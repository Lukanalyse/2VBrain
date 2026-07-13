import { API_BASE_URL } from '$lib/config/api';
import type {
  LinkableObject,
  LinkableType,
  LinkSearchResponse,
  ObjectRelations
} from '$lib/features/linking/types/linking';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers
    }
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(payload?.detail ?? 'Unable to update links.');
  }

  return response.json() as Promise<T>;
}

export async function searchLinkableObjects(
  query = '',
  types: LinkableType[] = []
): Promise<LinkableObject[]> {
  const params = new URLSearchParams();
  if (query) params.set('q', query);
  for (const type of types) params.append('types', type);
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await request<LinkSearchResponse>(`/links/search${suffix}`);
  return response.objects;
}

export async function getRelations(sourceId: string): Promise<ObjectRelations> {
  return request<ObjectRelations>(
    `/links/${encodeURIComponent(sourceId)}/relations`
  );
}

export async function createLinks(
  sourceId: string,
  targetIds: string[]
): Promise<void> {
  await request(`/links/${encodeURIComponent(sourceId)}`, {
    method: 'POST',
    body: JSON.stringify({ target_ids: targetIds, relation_type: 'related_to' })
  });
}
