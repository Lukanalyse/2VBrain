export const noteColors = [
  { id: 'cyan', label: 'Cyan', hsl: '190 90% 50%' },
  { id: 'teal', label: 'Teal', hsl: '166 72% 45%' },
  { id: 'violet', label: 'Violet', hsl: '265 82% 68%' },
  { id: 'amber', label: 'Amber', hsl: '40 92% 57%' },
  { id: 'rose', label: 'Rose', hsl: '345 82% 65%' },
  { id: 'slate', label: 'Slate', hsl: '215 18% 60%' }
] as const;

export function noteColorHsl(color?: string | null): string {
  return (
    noteColors.find((option) => option.id === color)?.hsl ?? noteColors[0].hsl
  );
}
