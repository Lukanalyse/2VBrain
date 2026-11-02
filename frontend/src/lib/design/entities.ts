import {
  BookOpenText,
  Boxes,
  Brain,
  FileText,
  Lightbulb,
  StickyNote
} from '@lucide/svelte';
import type { Component } from 'svelte';

import type { LinkableType } from '$lib/features/linking/types/linking';

export type EntityMeta = {
  /** Singular human label, e.g. "Paper". */
  label: string;
  /** Plural label for filters and section headers, e.g. "Papers". */
  plural: string;
  icon: Component;
  /** `hsl(var(--entity-*))` — for inline styles where a class won't do. */
  colorVar: string;
  /** Raw HSL channel variable, used by shared contextual surface styles. */
  hslVar: string;
  /** Tailwind text color, e.g. for the icon. */
  text: string;
  /** Tailwind left-border color, for the card identity edge. */
  borderLeft: string;
  /** Tailwind full-border color (discreet), for identity cards. */
  border: string;
  /** Stronger full-border color for the currently focused entity. */
  borderStrong: string;
  /** Tailwind faint tinted background (5–8%), for identity cards. */
  tint: string;
  /** Tailwind classes for a soft type badge. */
  badge: string;
  /** Focus/selection ring color for this type. */
  ring: string;
};

// NOTE: the class strings below are written as full literals (not composed at
// runtime) so Tailwind's content scanner keeps them in the build.
export const entityMeta: Record<LinkableType, EntityMeta> = {
  paper: {
    label: 'Paper',
    plural: 'Papers',
    icon: FileText,
    colorVar: 'hsl(var(--entity-paper))',
    hslVar: 'var(--entity-paper)',
    text: 'text-entity-paper',
    borderLeft: 'border-l-entity-paper',
    border: 'border-entity-paper/25',
    borderStrong: 'border-entity-paper/45',
    tint: 'bg-entity-paper/[0.06]',
    badge: 'bg-entity-paper/12 text-entity-paper',
    ring: 'ring-entity-paper/40'
  },
  concept: {
    label: 'Concept',
    plural: 'Concepts',
    icon: Brain,
    colorVar: 'hsl(var(--entity-concept))',
    hslVar: 'var(--entity-concept)',
    text: 'text-entity-concept',
    borderLeft: 'border-l-entity-concept',
    border: 'border-entity-concept/25',
    borderStrong: 'border-entity-concept/45',
    tint: 'bg-entity-concept/[0.06]',
    badge: 'bg-entity-concept/12 text-entity-concept',
    ring: 'ring-entity-concept/40'
  },
  project: {
    label: 'Project',
    plural: 'Projects',
    icon: Boxes,
    colorVar: 'hsl(var(--entity-project))',
    hslVar: 'var(--entity-project)',
    text: 'text-entity-project',
    borderLeft: 'border-l-entity-project',
    border: 'border-entity-project/25',
    borderStrong: 'border-entity-project/45',
    tint: 'bg-entity-project/[0.06]',
    badge: 'bg-entity-project/12 text-entity-project',
    ring: 'ring-entity-project/40'
  },
  brainstorm: {
    label: 'Brainstorm',
    plural: 'Brainstorms',
    icon: Lightbulb,
    colorVar: 'hsl(var(--entity-brainstorm))',
    hslVar: 'var(--entity-brainstorm)',
    text: 'text-entity-brainstorm',
    borderLeft: 'border-l-entity-brainstorm',
    border: 'border-entity-brainstorm/25',
    borderStrong: 'border-entity-brainstorm/45',
    tint: 'bg-entity-brainstorm/[0.06]',
    badge: 'bg-entity-brainstorm/12 text-entity-brainstorm',
    ring: 'ring-entity-brainstorm/40'
  },
  review: {
    label: 'Review',
    plural: 'Reviews',
    icon: BookOpenText,
    colorVar: 'hsl(var(--entity-review))',
    hslVar: 'var(--entity-review)',
    text: 'text-entity-review',
    borderLeft: 'border-l-entity-review',
    border: 'border-entity-review/25',
    borderStrong: 'border-entity-review/45',
    tint: 'bg-entity-review/[0.06]',
    badge: 'bg-entity-review/12 text-entity-review',
    ring: 'ring-entity-review/40'
  },
  note: {
    label: 'Note',
    plural: 'Notes',
    icon: StickyNote,
    colorVar: 'hsl(var(--entity-note))',
    hslVar: 'var(--entity-note)',
    text: 'text-entity-note',
    borderLeft: 'border-l-entity-note',
    border: 'border-entity-note/25',
    borderStrong: 'border-entity-note/45',
    tint: 'bg-entity-note/[0.06]',
    badge: 'bg-entity-note/12 text-entity-note',
    ring: 'ring-entity-note/40'
  }
};

export const entityTypes: LinkableType[] = [
  'paper',
  'concept',
  'project',
  'brainstorm',
  'review',
  'note'
];
