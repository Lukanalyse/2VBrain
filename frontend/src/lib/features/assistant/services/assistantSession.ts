import { browser } from '$app/environment';

import type { AssistantCitation } from '$lib/features/assistant/types/assistant';

export type AssistantChatMessage = {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  question?: string;
  citations: AssistantCitation[];
  saved?: boolean;
};

export type AssistantCitationFocus = {
  id: string;
  projectId: string;
  citation: AssistantCitation;
};

const MAX_MESSAGES = 24;
const conversationMemory = new Map<string, AssistantChatMessage[]>();
const citationMemory = new Map<string, AssistantCitationFocus>();

function conversationKey(projectId: string): string {
  return `research-os:assistant:conversation:${projectId}`;
}

function citationKey(id: string): string {
  return `research-os:assistant:citation:${id}`;
}

export function readAssistantConversation(
  projectId: string
): AssistantChatMessage[] {
  const inMemory = conversationMemory.get(projectId);
  if (inMemory) return inMemory;
  if (!browser) return [];

  try {
    const parsed = JSON.parse(
      window.sessionStorage.getItem(conversationKey(projectId)) ?? '[]'
    );
    if (!Array.isArray(parsed)) return [];
    const messages = parsed.filter(isAssistantChatMessage).slice(-MAX_MESSAGES);
    conversationMemory.set(projectId, messages);
    return messages;
  } catch {
    return [];
  }
}

export function writeAssistantConversation(
  projectId: string,
  messages: AssistantChatMessage[]
): void {
  const snapshot = messages.slice(-MAX_MESSAGES);
  conversationMemory.set(projectId, snapshot);
  if (!browser) return;
  window.sessionStorage.setItem(
    conversationKey(projectId),
    JSON.stringify(snapshot)
  );
}

export function clearAssistantConversation(projectId: string): void {
  conversationMemory.delete(projectId);
  if (!browser) return;
  window.sessionStorage.removeItem(conversationKey(projectId));
}

export function createCitationFocus(
  projectId: string,
  citation: AssistantCitation
): AssistantCitationFocus {
  const id =
    browser && 'randomUUID' in window.crypto
      ? window.crypto.randomUUID()
      : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  const focus = { id, projectId, citation };
  citationMemory.set(id, focus);
  if (browser) {
    window.sessionStorage.setItem(citationKey(id), JSON.stringify(focus));
  }
  return focus;
}

export function readCitationFocus(id: string): AssistantCitationFocus | null {
  const inMemory = citationMemory.get(id);
  if (inMemory) return inMemory;
  if (!browser) return null;

  try {
    const parsed = JSON.parse(
      window.sessionStorage.getItem(citationKey(id)) ?? 'null'
    );
    if (!isCitationFocus(parsed)) return null;
    citationMemory.set(id, parsed);
    return parsed;
  } catch {
    return null;
  }
}

function isAssistantChatMessage(value: unknown): value is AssistantChatMessage {
  if (!value || typeof value !== 'object') return false;
  const message = value as Partial<AssistantChatMessage>;
  return (
    typeof message.id === 'number' &&
    (message.role === 'user' || message.role === 'assistant') &&
    typeof message.content === 'string' &&
    Array.isArray(message.citations)
  );
}

function isCitationFocus(value: unknown): value is AssistantCitationFocus {
  if (!value || typeof value !== 'object') return false;
  const focus = value as Partial<AssistantCitationFocus>;
  return (
    typeof focus.id === 'string' &&
    typeof focus.projectId === 'string' &&
    Boolean(focus.citation && typeof focus.citation === 'object')
  );
}
