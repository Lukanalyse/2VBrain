import { API_BASE_URL } from '$lib/config/api';
import type { LinkableObject } from '$lib/features/linking/types/linking';

export type HomeSummary = {
  continue_reading: LinkableObject[];
  recent_papers: LinkableObject[];
  recent_concepts: LinkableObject[];
  recent_brainstorm: LinkableObject[];
  projects: LinkableObject[];
};

export type ActiveWorkspaceSummary = {
  reading: LinkableObject[];
  writing: LinkableObject[];
  projects: LinkableObject[];
  brainstorms: LinkableObject[];
};

export type WorkspaceObjectDetail = {
  object: LinkableObject;
  content: string;
};

export type WorkspaceMarkdownDocument = {
  object: LinkableObject;
  content: string;
};

export type WorkspaceNote = {
  id: string;
  title: string;
  path: string;
  is_primary: boolean;
};

export type WorkspaceNoteList = {
  object: LinkableObject;
  notes: WorkspaceNote[];
};

export type WorkspaceNoteDocument = {
  object: LinkableObject;
  note: WorkspaceNote;
  content: string;
};

export type ReadingStatus =
  'unread' | 'reading' | 'paused' | 'reviewed' | 'mastered';
export type CollectionStatus = 'inbox' | 'workspace' | 'library';

export type WorkspaceStatusResponse = {
  object: LinkableObject;
  status: ReadingStatus;
};

export type WorkspaceCollectionResponse = {
  object: LinkableObject;
  collection_status: CollectionStatus;
};

export type WorkspaceProjectResponse = {
  object: LinkableObject;
  project_id: string;
};

export type WorkspaceResearchMetadata = {
  status: ReadingStatus;
  reading_progress: number;
  importance: string;
  priority: string;
  domain: string;
  method: string;
  difficulty: string;
  personal_tags: string;
};

export type WorkspaceResearchMetadataResponse = {
  object: LinkableObject;
  metadata: Record<string, string | number | null>;
};

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
    throw new Error(payload?.detail ?? 'Workspace request failed.');
  }

  return response.json() as Promise<T>;
}

export function getHomeSummary(): Promise<HomeSummary> {
  return request<HomeSummary>('/workspace/home');
}

export function getActiveWorkspace(): Promise<ActiveWorkspaceSummary> {
  return request<ActiveWorkspaceSummary>('/workspace/active');
}

export function getWorkspaceMarkdown(
  objectId: string
): Promise<WorkspaceMarkdownDocument> {
  return request<WorkspaceMarkdownDocument>(
    `/workspace/objects/${encodeURIComponent(objectId)}/markdown`
  );
}

export function saveWorkspaceMarkdown(
  objectId: string,
  content: string
): Promise<WorkspaceMarkdownDocument> {
  return request<WorkspaceMarkdownDocument>(
    `/workspace/objects/${encodeURIComponent(objectId)}/markdown`,
    {
      method: 'PUT',
      body: JSON.stringify({ content })
    }
  );
}

export function listWorkspaceNotes(
  objectId: string
): Promise<WorkspaceNoteList> {
  return request<WorkspaceNoteList>(
    `/workspace/objects/${encodeURIComponent(objectId)}/notes`
  );
}

export function createWorkspaceNote(
  objectId: string,
  title: string
): Promise<WorkspaceNoteDocument> {
  return request<WorkspaceNoteDocument>(
    `/workspace/objects/${encodeURIComponent(objectId)}/notes`,
    {
      method: 'POST',
      body: JSON.stringify({ title })
    }
  );
}

export function getWorkspaceNote(
  objectId: string,
  noteId: string
): Promise<WorkspaceNoteDocument> {
  return request<WorkspaceNoteDocument>(
    `/workspace/objects/${encodeURIComponent(objectId)}/notes/${encodeURIComponent(noteId)}`
  );
}

export function saveWorkspaceNote(
  objectId: string,
  noteId: string,
  content: string
): Promise<WorkspaceNoteDocument> {
  return request<WorkspaceNoteDocument>(
    `/workspace/objects/${encodeURIComponent(objectId)}/notes/${encodeURIComponent(noteId)}`,
    {
      method: 'PUT',
      body: JSON.stringify({ content })
    }
  );
}

export function renameWorkspaceNote(
  objectId: string,
  noteId: string,
  title: string
): Promise<WorkspaceNoteDocument> {
  return request<WorkspaceNoteDocument>(
    `/workspace/objects/${encodeURIComponent(objectId)}/notes/${encodeURIComponent(noteId)}`,
    {
      method: 'PATCH',
      body: JSON.stringify({ title })
    }
  );
}

export function duplicateWorkspaceNote(
  objectId: string,
  noteId: string
): Promise<WorkspaceNoteDocument> {
  return request<WorkspaceNoteDocument>(
    `/workspace/objects/${encodeURIComponent(objectId)}/notes/${encodeURIComponent(noteId)}/duplicate`,
    {
      method: 'POST'
    }
  );
}

export function deleteWorkspaceNote(
  objectId: string,
  noteId: string
): Promise<WorkspaceNoteList> {
  return request<WorkspaceNoteList>(
    `/workspace/objects/${encodeURIComponent(objectId)}/notes/${encodeURIComponent(noteId)}`,
    {
      method: 'DELETE'
    }
  );
}

export function getWorkspacePdfUrl(objectId: string): string {
  return `${API_BASE_URL}/workspace/objects/${encodeURIComponent(objectId)}/pdf`;
}

export function openWorkspacePdf(
  objectId: string
): Promise<{ status: string }> {
  return request<{ status: string }>(
    `/workspace/objects/${encodeURIComponent(objectId)}/open-pdf`,
    {
      method: 'POST'
    }
  );
}

export function updateWorkspaceStatus(
  objectId: string,
  status: ReadingStatus
): Promise<WorkspaceStatusResponse> {
  return request<WorkspaceStatusResponse>(
    `/workspace/objects/${encodeURIComponent(objectId)}/status`,
    {
      method: 'PUT',
      body: JSON.stringify({ status })
    }
  );
}

export function updateWorkspaceCollection(
  objectId: string,
  collectionStatus: CollectionStatus
): Promise<WorkspaceCollectionResponse> {
  return request<WorkspaceCollectionResponse>(
    `/workspace/objects/${encodeURIComponent(objectId)}/collection`,
    {
      method: 'PUT',
      body: JSON.stringify({ collection_status: collectionStatus })
    }
  );
}

export function setWorkspaceProject(
  objectId: string,
  projectId: string
): Promise<WorkspaceProjectResponse> {
  return request<WorkspaceProjectResponse>(
    `/workspace/objects/${encodeURIComponent(objectId)}/project`,
    {
      method: 'PUT',
      body: JSON.stringify({ project_id: projectId })
    }
  );
}

export function updateWorkspaceResearchMetadata(
  objectId: string,
  metadata: WorkspaceResearchMetadata
): Promise<WorkspaceResearchMetadataResponse> {
  return request<WorkspaceResearchMetadataResponse>(
    `/workspace/objects/${encodeURIComponent(objectId)}/research-metadata`,
    {
      method: 'PUT',
      body: JSON.stringify(metadata)
    }
  );
}

export async function setObjectTags(
  objectId: string,
  tags: string[]
): Promise<{ object: LinkableObject; tags: string[] }> {
  return request<{ object: LinkableObject; tags: string[] }>(
    `/workspace/objects/${encodeURIComponent(objectId)}/tags`,
    {
      method: 'PUT',
      body: JSON.stringify({ tags })
    }
  );
}

export function renameObject(
  objectId: string,
  title: string
): Promise<{ object: LinkableObject }> {
  return request<{ object: LinkableObject }>(
    `/workspace/objects/${encodeURIComponent(objectId)}/rename`,
    { method: 'PUT', body: JSON.stringify({ title }) }
  );
}

export function duplicateObject(
  objectId: string
): Promise<{ object: LinkableObject }> {
  return request<{ object: LinkableObject }>(
    `/workspace/objects/${encodeURIComponent(objectId)}/duplicate`,
    { method: 'POST', body: JSON.stringify({}) }
  );
}

export async function deleteObject(objectId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/workspace/objects/${encodeURIComponent(objectId)}`,
    { method: 'DELETE' }
  );
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(payload?.detail ?? 'Unable to delete this object.');
  }
}

export async function listProjects(): Promise<LinkableObject[]> {
  const response = await request<{ objects: LinkableObject[] }>(
    '/workspace/projects'
  );
  return response.objects;
}

export function createProject(title: string): Promise<WorkspaceObjectDetail> {
  return request<WorkspaceObjectDetail>('/workspace/projects', {
    method: 'POST',
    body: JSON.stringify({ title })
  });
}

export async function listBrainstorm(): Promise<LinkableObject[]> {
  const response = await request<{ objects: LinkableObject[] }>(
    '/workspace/brainstorm'
  );
  return response.objects;
}

export function createBrainstorm(
  title: string
): Promise<WorkspaceObjectDetail> {
  return request<WorkspaceObjectDetail>('/workspace/brainstorm', {
    method: 'POST',
    body: JSON.stringify({ title })
  });
}
