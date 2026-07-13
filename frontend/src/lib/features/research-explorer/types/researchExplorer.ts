import type {
  LinkableObject,
  LinkableType
} from '$lib/features/linking/types/linking';

export type ExplorerObjectDetail = {
  object: LinkableObject;
  description: string;
  parent: string;
  tags: string[];
  metadata: Record<string, string>;
  related: Record<LinkableType, LinkableObject[]>;
  backlinks: Record<LinkableType, LinkableObject[]>;
  all_related: LinkableObject[];
  corpus?: Partial<Record<LinkableType, CorpusEntry[]>>;
};

export type ExplorerSearchResponse = {
  objects: LinkableObject[];
};

export type CorpusEntry = {
  object: LinkableObject;
  roles: string[];
};
