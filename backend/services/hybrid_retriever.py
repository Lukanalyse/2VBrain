import math
from dataclasses import dataclass

from repositories.assistant_repository import AssistantChunkRecord, AssistantRepository


@dataclass(frozen=True)
class RetrievedChunk:
    record: AssistantChunkRecord
    score: float


class HybridRetriever:
    def __init__(self, repository: AssistantRepository) -> None:
        self._repository = repository

    def retrieve(
        self,
        *,
        project_id: str,
        query: str,
        query_embedding: list[float],
        limit: int = 10,
        character_budget: int = 18000,
    ) -> list[RetrievedChunk]:
        lexical = self._repository.lexical_chunks(project_id, query)
        candidates = self._repository.project_chunks(project_id)
        semantic = sorted(
            (
                (self._cosine(query_embedding, list(record.embedding)), record)
                for record in candidates
                if record.embedding
            ),
            key=lambda item: item[0],
            reverse=True,
        )[:30]

        scores: dict[int, float] = {}
        records: dict[int, AssistantChunkRecord] = {}
        for rank, record in enumerate(lexical, start=1):
            records[record.chunk_id] = record
            scores[record.chunk_id] = scores.get(record.chunk_id, 0.0) + 1 / (60 + rank)
        for rank, (similarity, record) in enumerate(semantic, start=1):
            if similarity < 0.20:
                continue
            records[record.chunk_id] = record
            scores[record.chunk_id] = (
                scores.get(record.chunk_id, 0.0) + 1 / (60 + rank) + max(similarity, 0.0) * 0.01
            )

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        selected: list[RetrievedChunk] = []
        used_characters = 0
        for chunk_id, score in ranked:
            record = records[chunk_id]
            if selected and used_characters + len(record.content) > character_budget:
                continue
            selected.append(RetrievedChunk(record=record, score=score))
            used_characters += len(record.content)
            if len(selected) >= limit:
                break
        return selected

    def _cosine(self, left: list[float], right: list[float]) -> float:
        if not left or len(left) != len(right):
            return -1.0
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return -1.0
        return sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)
