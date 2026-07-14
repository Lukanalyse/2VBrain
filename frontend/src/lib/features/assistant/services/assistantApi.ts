import { API_BASE_URL } from '$lib/config/api';
import type {
  AssistantConfig,
  AssistantHistoryMessage,
  AssistantStatus,
  ProjectAssistantResponse,
  ProjectIndexStatus
} from '$lib/features/assistant/types/assistant';

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
    throw new Error(payload?.detail ?? 'Local AI request failed.');
  }

  return response.json() as Promise<T>;
}

export function getAssistantStatus(): Promise<AssistantStatus> {
  return request<AssistantStatus>('/assistant/status');
}

export function saveAssistantConfig(
  config: Pick<
    AssistantConfig,
    'chat_model' | 'embedding_model' | 'context_length'
  >
): Promise<AssistantConfig> {
  return request<AssistantConfig>('/assistant/config', {
    method: 'PUT',
    body: JSON.stringify(config)
  });
}

export function getProjectIndex(
  projectId: string
): Promise<ProjectIndexStatus> {
  return request<ProjectIndexStatus>(
    `/assistant/projects/${encodeURIComponent(projectId)}/index`
  );
}

export function indexProject(projectId: string): Promise<ProjectIndexStatus> {
  return request<ProjectIndexStatus>(
    `/assistant/projects/${encodeURIComponent(projectId)}/index`,
    { method: 'POST' }
  );
}

export function queryProject(
  projectId: string,
  question: string,
  history: AssistantHistoryMessage[]
): Promise<ProjectAssistantResponse> {
  return request<ProjectAssistantResponse>(
    `/assistant/projects/${encodeURIComponent(projectId)}/query`,
    {
      method: 'POST',
      body: JSON.stringify({ question, history })
    }
  );
}
