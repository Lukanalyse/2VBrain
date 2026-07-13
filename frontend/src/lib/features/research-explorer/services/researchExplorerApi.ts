import { API_BASE_URL } from '$lib/config/api';
import type {
  LinkableObject,
  LinkableType
} from '$lib/features/linking/types/linking';
import type {
  ExplorerObjectDetail,
  ExplorerSearchResponse
} from '$lib/features/research-explorer/types/researchExplorer';

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(payload?.detail ?? 'Research Explorer request failed.');
  }
  return response.json() as Promise<T>;
}

export async function searchExplorer(
  query = '',
  types: LinkableType[] = []
): Promise<LinkableObject[]> {
  const params = new URLSearchParams();
  if (query) params.set('q', query);
  for (const type of types) params.append('types', type);
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await request<ExplorerSearchResponse>(
    `/research-explorer/search${suffix}`
  );
  return response.objects;
}

export function getExplorerDetail(
  objectId: string
): Promise<ExplorerObjectDetail> {
  return request<ExplorerObjectDetail>(
    `/research-explorer/objects/${encodeURIComponent(objectId)}`
  );
}
