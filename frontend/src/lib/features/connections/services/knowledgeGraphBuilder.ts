import { entityTypes } from '$lib/design/entities';
import type {
  LinkableObject,
  LinkableType
} from '$lib/features/linking/types/linking';
import type {
  ConnectionGraphData,
  ConnectionGraphEdge,
  ConnectionType,
  ObjectConnection
} from '$lib/features/connections/types/connections';
import type {
  KnowledgeGraphFilters,
  LocalGraph,
  LocalGraphEdge,
  LocalGraphNode,
  StructureConnection,
  StructureGroup
} from '$lib/features/connections/types/knowledgeGraph';

export function createDefaultFilters(
  relationTypes: ConnectionType[]
): KnowledgeGraphFilters {
  return {
    objectTypes: new Set<LinkableType>(entityTypes),
    relationTypes: new Set<ConnectionType>(relationTypes)
  };
}

export function buildStructureGroups(
  current: LinkableObject,
  outgoing: ObjectConnection[],
  incoming: ObjectConnection[],
  filters: KnowledgeGraphFilters
): StructureGroup[] {
  const items: StructureConnection[] = [
    ...outgoing.map((connection) => ({
      connection,
      object: connection.target,
      direction: 'outgoing' as const
    })),
    ...incoming.map((connection) => ({
      connection,
      object: connection.source,
      direction: 'incoming' as const
    }))
  ].filter(
    (item) =>
      item.object.id !== current.id &&
      filters.objectTypes.has(item.object.type) &&
      filters.relationTypes.has(item.connection.relation_type)
  );

  return entityTypes
    .map((type) => ({
      type,
      items: items
        .filter((item) => item.object.type === type)
        .sort((a, b) => a.object.title.localeCompare(b.object.title))
    }))
    .filter((group) => group.items.length > 0);
}

export function buildLocalGraph(
  graph: ConnectionGraphData,
  current: LinkableObject,
  filters: KnowledgeGraphFilters,
  depthLimit: number
): LocalGraph {
  const objectById = new Map<string, LinkableObject>(
    graph.nodes.map((node) => [
      node.id,
      {
        id: node.id,
        type: node.type,
        title: node.title,
        subtitle: '',
        markdown_path: ''
      }
    ])
  );
  objectById.set(current.id, current);

  const adjacency = new Map<string, ConnectionGraphEdge[]>();
  for (const edge of graph.edges) {
    if (!filters.relationTypes.has(edge.relation_type)) continue;
    const source = objectById.get(edge.source_id);
    const target = objectById.get(edge.target_id);
    if (!source || !target) continue;
    if (
      !filters.objectTypes.has(source.type) ||
      !filters.objectTypes.has(target.type)
    ) {
      continue;
    }
    adjacency.set(edge.source_id, [
      ...(adjacency.get(edge.source_id) ?? []),
      edge
    ]);
    adjacency.set(edge.target_id, [
      ...(adjacency.get(edge.target_id) ?? []),
      edge
    ]);
  }

  const depths = new Map<string, number>([[current.id, 0]]);
  const queue = [current.id];
  while (queue.length > 0) {
    const objectId = queue.shift();
    if (!objectId) continue;
    const depth = depths.get(objectId) ?? 0;
    if (depth >= depthLimit) continue;

    for (const edge of adjacency.get(objectId) ?? []) {
      const nextId =
        edge.source_id === objectId ? edge.target_id : edge.source_id;
      if (depths.has(nextId)) continue;
      depths.set(nextId, depth + 1);
      queue.push(nextId);
    }
  }

  const visibleIds = new Set(depths.keys());
  const edges: LocalGraphEdge[] = graph.edges
    .filter(
      (edge) =>
        visibleIds.has(edge.source_id) &&
        visibleIds.has(edge.target_id) &&
        filters.relationTypes.has(edge.relation_type)
    )
    .map((edge) => {
      const source = objectById.get(edge.source_id);
      const target = objectById.get(edge.target_id);
      if (!source || !target) return null;
      return { ...edge, source, target };
    })
    .filter((edge): edge is LocalGraphEdge => edge !== null);

  const relationCounts = new Map<string, number>();
  for (const edge of edges) {
    relationCounts.set(
      edge.source_id,
      (relationCounts.get(edge.source_id) ?? 0) + 1
    );
    relationCounts.set(
      edge.target_id,
      (relationCounts.get(edge.target_id) ?? 0) + 1
    );
  }

  const nodes: LocalGraphNode[] = [...visibleIds]
    .map((id) => {
      const object = objectById.get(id);
      if (!object) return null;
      return {
        ...object,
        depth: depths.get(id) ?? 0,
        relation_count: relationCounts.get(id) ?? 0
      };
    })
    .filter((node): node is LocalGraphNode => node !== null)
    .sort((a, b) => a.depth - b.depth || a.title.localeCompare(b.title));

  return { nodes, edges };
}
