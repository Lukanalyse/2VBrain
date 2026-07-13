import type {
  LinkableObject,
  LinkableType
} from '$lib/features/linking/types/linking';

export type ConnectionType =
  | 'references'
  | 'related'
  | 'explains'
  | 'uses'
  | 'extends'
  | 'contradicts'
  | 'inspired_by';

export type ObjectConnection = {
  id: string;
  source: LinkableObject;
  target: LinkableObject;
  relation_type: ConnectionType;
  created_at: string;
};

export type ConnectionTypeDefinition = {
  id: ConnectionType;
  label: string;
  inverse_label: string;
  description: string;
  weight: number;
};

export type ConnectionList = {
  current: LinkableObject;
  outgoing: ObjectConnection[];
  incoming: ObjectConnection[];
};

export type ConnectionSearchResponse = {
  objects: LinkableObject[];
};

export type ConnectionTypesResponse = {
  relation_types: ConnectionTypeDefinition[];
};

export type ConnectionGraphNode = {
  id: string;
  type: LinkableType;
  title: string;
};

export type ConnectionGraphEdge = {
  id: string;
  source_id: string;
  target_id: string;
  relation_type: ConnectionType;
};

export type ConnectionGraphData = {
  nodes: ConnectionGraphNode[];
  edges: ConnectionGraphEdge[];
};

export const connectionTypes: ConnectionType[] = [
  'references',
  'related',
  'explains',
  'uses',
  'extends',
  'contradicts',
  'inspired_by'
];

export const connectionLabels: Record<ConnectionType, string> = {
  references: 'References',
  related: 'Related',
  explains: 'Explains',
  uses: 'Uses',
  extends: 'Extends',
  contradicts: 'Contradicts',
  inspired_by: 'Inspired by'
};

export const defaultConnectionTypeDefinitions: ConnectionTypeDefinition[] = [
  {
    id: 'references',
    label: 'References',
    inverse_label: 'Referenced by',
    description: 'The source explicitly cites or points to the target.',
    weight: 2
  },
  {
    id: 'related',
    label: 'Related',
    inverse_label: 'Related',
    description: 'The source and target are meaningfully associated.',
    weight: 1
  },
  {
    id: 'explains',
    label: 'Explains',
    inverse_label: 'Explained by',
    description: 'The source clarifies the target.',
    weight: 3
  },
  {
    id: 'uses',
    label: 'Uses',
    inverse_label: 'Used by',
    description: 'The source relies on the target.',
    weight: 3
  },
  {
    id: 'extends',
    label: 'Extends',
    inverse_label: 'Extended by',
    description: 'The source builds on the target.',
    weight: 3
  },
  {
    id: 'contradicts',
    label: 'Contradicts',
    inverse_label: 'Contradicted by',
    description: 'The source conflicts with the target.',
    weight: 4
  },
  {
    id: 'inspired_by',
    label: 'Inspired by',
    inverse_label: 'Inspires',
    description: 'The source was influenced by the target.',
    weight: 2
  }
];
