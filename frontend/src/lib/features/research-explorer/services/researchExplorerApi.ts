import { API_BASE_URL } from '$lib/config/api';
import type {
  LinkableObject,
  LinkableType
} from '$lib/features/linking/types/linking';
import type {
  ExplorerObjectDetail,
  ExplorerSearchResponse
} from '$lib/features/research-explorer/types/researchExplorer';
import { cachedQuery } from '$lib/services/queryCache';

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { signal });
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
  types: LinkableType[] = [],
  signal?: AbortSignal
): Promise<LinkableObject[]> {
  const params = new URLSearchParams();
  if (query) params.set('q', query);
  for (const type of types) params.append('types', type);
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const path = `/research-explorer/search${suffix}`;
  const response = signal
    ? await request<ExplorerSearchResponse>(path, signal)
    : await cachedQuery(
        `explorer:search:${path}`,
        () => request<ExplorerSearchResponse>(path),
        query ? 1_500 : 3_000
      );
  return response.objects;
}

export function getExplorerDetail(
  objectId: string,
  signal?: AbortSignal
): Promise<ExplorerObjectDetail> {
  const path = `/research-explorer/objects/${encodeURIComponent(objectId)}`;
  return signal
    ? request<ExplorerObjectDetail>(path, signal)
    : cachedQuery(
        `explorer:detail:${objectId}`,
        () => request<ExplorerObjectDetail>(path),
        3_000
      );
}
