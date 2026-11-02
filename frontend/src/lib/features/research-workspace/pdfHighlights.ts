import { API_BASE_URL } from '$lib/config/api';

export const highlightColors = [
  { id: 'yellow', label: 'Yellow', value: '#facc15' },
  { id: 'green', label: 'Green', value: '#4ade80' },
  { id: 'blue', label: 'Blue', value: '#60a5fa' },
  { id: 'pink', label: 'Pink', value: '#f472b6' },
  { id: 'violet', label: 'Violet', value: '#a78bfa' }
] as const;
export type HighlightColor = (typeof highlightColors)[number]['id'];
export type PdfHighlight = {
  id: string;
  page: number;
  color: HighlightColor;
  text: string;
  rects: { x: number; y: number; width: number; height: number }[];
};
export function highlightValue(color: HighlightColor): string {
  return highlightColors.find((item) => item.id === color)?.value ?? '#facc15';
}
export async function pdfHighlights(
  objectId: string,
  highlights?: PdfHighlight[]
): Promise<PdfHighlight[]> {
  const response = await fetch(
    `${API_BASE_URL}/workspace/objects/${encodeURIComponent(objectId)}/pdf-highlights`,
    highlights === undefined
      ? {}
      : {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ highlights })
        }
  );
  if (!response.ok)
    throw new Error('Unable to save or load PDF highlights. Please retry.');
  return (await response.json()).highlights;
}
