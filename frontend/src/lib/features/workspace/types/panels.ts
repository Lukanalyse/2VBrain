import type { SaveState } from '$lib/features/knowledge/types/knowledge';
import type { LinkableObject } from '$lib/features/linking/types/linking';
import type { ExplorerObjectDetail } from '$lib/features/research-explorer/types/researchExplorer';
import type {
  ReadingStatus,
  WorkspaceNote
} from '$lib/features/workspace/services/workspaceApi';

export type WorkspacePanelContext = {
  object: LinkableObject;
  detail: ExplorerObjectDetail | null;
  content: string;
  saveState: SaveState;
  notes?: WorkspaceNote[];
  activeNoteId?: string;
  updateContent: (value: string) => void;
  openObject: (object: LinkableObject) => Promise<void>;
  updateReadingStatus: (status: ReadingStatus) => Promise<void>;
  searchObjects: (query: string) => Promise<LinkableObject[]>;
  appendReadingNote: (text: string) => void;
  createConceptFromSelection: (text: string) => Promise<void>;
  createBrainstormFromSelection: (text: string) => Promise<void>;
  createProjectFromSelection: (text: string) => Promise<void>;
  createReviewFromSelection: (text: string) => Promise<void>;
  linkSelectionToConcept: (text: string) => Promise<void>;
  openPdf: () => Promise<void>;
  createConceptFromTitle: (title: string) => Promise<LinkableObject | null>;
  createProjectFromTitle: (title: string) => Promise<LinkableObject | null>;
  createReviewFromTitle: (title: string) => Promise<LinkableObject | null>;
  createBrainstormFromTitle: (title: string) => Promise<LinkableObject | null>;
  linkObjectToTarget: (target: LinkableObject) => Promise<void>;
  refreshObject: () => Promise<void>;
};
