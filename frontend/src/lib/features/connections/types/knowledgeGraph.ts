import type {
  LinkableObject,
  LinkableType
} from '$lib/features/linking/types/linking';
import type {
  ConnectionGraphEdge,
  ConnectionType,
  ObjectConnection
} from '$lib/features/connections/types/connections';

export type KnowledgeGraphFilters = {
  objectTypes: Set<LinkableType>;
  relationTypes: Set<ConnectionType>;
};

export type StructureConnection = {
  connection: ObjectConnection;
  object: LinkableObject;
  direction: 'outgoing' | 'incoming';
};

export type StructureGroup = {
  type: LinkableType;
  items: StructureConnection[];
};

export type LocalGraphNode = LinkableObject & {
  depth: number;
  relation_count: number;
};

export type LocalGraphEdge = ConnectionGraphEdge & {
  source: LinkableObject;
  target: LinkableObject;
};

export type LocalGraph = {
  nodes: LocalGraphNode[];
  edges: LocalGraphEdge[];
};
