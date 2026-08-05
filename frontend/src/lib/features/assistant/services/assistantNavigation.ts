import { createCitationFocus } from '$lib/features/assistant/services/assistantSession';
import type { AssistantCitation } from '$lib/features/assistant/types/assistant';

export function assistantProjectUrl(projectId: string): string {
  return `/assistant?project=${encodeURIComponent(projectId)}`;
}

export function citationWorkspaceUrl(
  projectId: string,
  citation: AssistantCitation
): string {
  const focus = createCitationFocus(projectId, citation);
  const params = new URLSearchParams({
    open: citation.object.id,
    citation: focus.id,
    assistantProject: projectId,
    sourceKind: citation.source_kind
  });
  if (citation.page_number) {
    params.set('page', String(citation.page_number));
  }
  return `/workspace?${params.toString()}`;
}
