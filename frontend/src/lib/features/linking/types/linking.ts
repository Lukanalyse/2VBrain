export type LinkableType =
  | 'paper'
  | 'concept'
  | 'project'
  | 'brainstorm'
  | 'review'
  | 'note';

export type LinkableObject = {
  id: string;
  type: LinkableType;
  title: string;
  subtitle: string;
  markdown_path: string;
  search_excerpt?: string;
  collection_status?: 'inbox' | 'workspace' | 'library' | null;
  project_id?: string | null;
};

export type ObjectRelations = {
  source: LinkableObject;
  outgoing: Record<LinkableType, LinkableObject[]>;
  incoming: Record<LinkableType, LinkableObject[]>;
};

export type LinkSearchResponse = {
  objects: LinkableObject[];
};
