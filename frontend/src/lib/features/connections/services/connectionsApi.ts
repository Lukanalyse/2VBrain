import { API_BASE_URL } from '$lib/config/api';
import type {
  LinkableObject,
  LinkableType
} from '$lib/features/linking/types/linking';
import type {
  ConnectionList,
  ConnectionGraphData,
  ConnectionSearchResponse,
  ConnectionTypesResponse,
  ConnectionType,
  ObjectConnection
} from '$lib/features/connections/types/connections';

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
    throw new Error(payload?.detail ?? 'Connections request failed.');
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function searchConnectionObjects(
  query = '',
  types: LinkableType[] = [],
  signal?: AbortSignal
): Promise<LinkableObject[]> {
  const params = new URLSearchParams();
  if (query) params.set('q', query);
  for (const type of types) params.append('types', type);
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await request<ConnectionSearchResponse>(
    `/connections/search${suffix}`,
    { signal }
  );
  return response.objects;
}

export function getObjectConnections(
  objectId: string,
  signal?: AbortSignal
): Promise<ConnectionList> {
  return request<ConnectionList>(
    `/connections/${encodeURIComponent(objectId)}`,
    { signal }
  );
}

export async function getConnectionTypes(): Promise<ConnectionTypesResponse> {
  return request<ConnectionTypesResponse>('/connections/relation-types');
}

export function getConnectionGraph(): Promise<ConnectionGraphData> {
  return request<ConnectionGraphData>('/connections/graph');
}

export function createConnection(
  sourceId: string,
  targetId: string,
  relationType: ConnectionType
): Promise<ObjectConnection> {
  return request<ObjectConnection>(
    `/connections/${encodeURIComponent(sourceId)}`,
    {
      method: 'POST',
      body: JSON.stringify({ target_id: targetId, relation_type: relationType })
    }
  );
}

export function deleteConnection(connectionId: string): Promise<void> {
  return request<void>(`/connections/${encodeURIComponent(connectionId)}`, {
    method: 'DELETE'
  });
}
