import re
from pathlib import Path

from sqlalchemy.orm import Session

from schemas.connections import (
    ConnectionGraphEdge,
    ConnectionGraphNode,
    ConnectionGraphResponse,
    ConnectionListResponse,
    ConnectionResponse,
    ConnectionType,
    ConnectionTypeDefinition,
)
from schemas.linking import LinkableObject, LinkableType
from services.linking_engine import LinkingEngine, LinkingEngineError


class ConnectionManagerError(Exception):
    pass


class ConnectionManager:
    """Markdown-backed relation layer for research objects.

    SQLite may index these edges later, but it must not own them. The durable
    relation is the Obsidian wikilink in the source object's Markdown file.
    """

    def __init__(self, *, db: Session, linking_engine: LinkingEngine) -> None:
        self._db = db
        self._linking_engine = linking_engine

    def search(
        self, query: str = "", object_types: list[LinkableType] | None = None
    ) -> list[LinkableObject]:
        return self._linking_engine.search(query, object_types)

    def relation_types(self) -> list[ConnectionTypeDefinition]:
        return [
            ConnectionTypeDefinition(
                id=ConnectionType.related,
                label="Markdown Link",
                inverse_label="Linked from",
                description="A durable Obsidian wikilink found in the Vault Markdown.",
                weight=1,
            )
        ]

    def list_connections(self, object_id: str) -> ConnectionListResponse:
        try:
            relations = self._linking_engine.get_relations(object_id)
        except LinkingEngineError as error:
            raise ConnectionManagerError(str(error)) from error

        source = relations.source
        outgoing = [
            self._response(source, target)
            for group in relations.outgoing.values()
            for target in group
        ]
        incoming = [
            self._response(candidate, source)
            for group in relations.incoming.values()
            for candidate in group
        ]
        return ConnectionListResponse(
            current=source,
            outgoing=sorted(outgoing, key=lambda item: (item.target.type.value, item.target.title)),
            incoming=sorted(incoming, key=lambda item: (item.source.type.value, item.source.title)),
        )

    def create_connection(
        self,
        *,
        source_id: str,
        target_id: str,
        relation_type: ConnectionType,
    ) -> ConnectionResponse:
        if source_id == target_id:
            raise ConnectionManagerError("An object cannot be connected to itself.")
        try:
            targets = self._linking_engine.link(source_id, [target_id])
            source = self._get_object(source_id)
        except LinkingEngineError as error:
            raise ConnectionManagerError(str(error)) from error
        if not targets:
            raise ConnectionManagerError("Connection target not found.")
        return self._response(source, targets[0])

    def delete_connection(self, connection_id: str) -> None:
        source_id, target_id = self._parse_edge_id(connection_id)
        source = self._get_object(source_id)
        target = self._get_object(target_id)
        path = Path(source.markdown_path).expanduser().resolve()
        content = path.read_text(encoding="utf-8")
        next_content = self._remove_wikilink(content, target)
        if next_content == content:
            raise ConnectionManagerError("Connection not found.")
        path.write_text(next_content, encoding="utf-8")
        self._linking_engine.invalidate_path(path)

    def graph_data(self) -> ConnectionGraphResponse:
        objects = self._linking_engine.search("")
        object_by_id = {item.id: item for item in objects}
        edges_by_id: dict[str, ConnectionGraphEdge] = {}

        for source in objects:
            relations = self._linking_engine.get_relations(source.id)
            for group in relations.outgoing.values():
                for target in group:
                    edge_id = self._edge_id(source.id, target.id)
                    edges_by_id[edge_id] = ConnectionGraphEdge(
                        id=edge_id,
                        source_id=source.id,
                        target_id=target.id,
                        relation_type=ConnectionType.related,
                    )

        connected_ids = {
            object_id
            for edge in edges_by_id.values()
            for object_id in (edge.source_id, edge.target_id)
        }
        nodes = [
            ConnectionGraphNode(id=item.id, type=item.type.value, title=item.title)
            for item in sorted(
                (object_by_id[object_id] for object_id in connected_ids if object_id in object_by_id),
                key=lambda entry: (entry.type.value, entry.title.lower()),
            )
        ]
        return ConnectionGraphResponse(
            nodes=nodes,
            edges=sorted(edges_by_id.values(), key=lambda edge: edge.id),
        )

    def _response(self, source: LinkableObject, target: LinkableObject) -> ConnectionResponse:
        return ConnectionResponse(
            id=self._edge_id(source.id, target.id),
            source=source,
            target=target,
            relation_type=ConnectionType.related,
        )

    def _get_object(self, object_id: str) -> LinkableObject:
        try:
            for item in self._linking_engine.search(""):
                if item.id == object_id:
                    return item
        except LinkingEngineError as error:
            raise ConnectionManagerError(str(error)) from error
        raise ConnectionManagerError("Object not found.")

    def _edge_id(self, source_id: str, target_id: str) -> str:
        return f"{source_id}=>{target_id}"

    def _parse_edge_id(self, edge_id: str) -> tuple[str, str]:
        if "=>" not in edge_id:
            raise ConnectionManagerError("Invalid Markdown connection id.")
        source_id, target_id = edge_id.split("=>", 1)
        return source_id, target_id

    def _remove_wikilink(self, content: str, target: LinkableObject) -> str:
        labels = {target.title, Path(target.markdown_path).stem}

        pattern = re.compile(r"\[\[([^\]]+)\]\]")
        lines = []
        for line in content.splitlines():
            matches = list(pattern.finditer(line))
            linked_labels = {
                match.group(1).split("|", 1)[0].split("#", 1)[0].strip()
                for match in matches
            }
            if linked_labels & labels and re.fullmatch(r"\s*[-*]\s+\[\[[^\]]+\]\]\s*", line):
                continue

            def replace_match(match: re.Match[str]) -> str:
                label = match.group(1).split("|", 1)[0].split("#", 1)[0].strip()
                return "" if label in labels else match.group(0)

            lines.append(pattern.sub(replace_match, line))
        return "\n".join(lines) + ("\n" if content.endswith("\n") else "")
