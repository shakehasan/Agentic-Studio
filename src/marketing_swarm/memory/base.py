"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from marketing_swarm.schemas.common import new_id, utc_now


@dataclass(slots=True)
class MemoryRecord:
    """Record stored in a memory tier."""

    key: str
    value: dict[str, Any]
    namespace: str = "default"
    id: str = field(default_factory=lambda: new_id("mem"))
    created_at: object = field(default_factory=utc_now)
    score: float = 1.0


class MemoryTier:
    """Base in-memory tier with namespace search."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._records: list[MemoryRecord] = []

    def put(self, key: str, value: dict[str, Any], namespace: str = "default", score: float = 1.0) -> MemoryRecord:
        """Store a memory record."""
        record = MemoryRecord(key=key, value=value, namespace=namespace, score=score)
        self._records.append(record)
        return record

    def get(self, key: str, namespace: str = "default") -> MemoryRecord | None:
        """Get the newest record for a key."""
        for record in reversed(self._records):
            if record.key == key and record.namespace == namespace:
                return record
        return None

    def search(self, query: str, namespace: str | None = None, limit: int = 10) -> list[MemoryRecord]:
        """Search records by lexical overlap."""
        terms = {term.lower() for term in query.split() if len(term) > 2}
        scored: list[tuple[float, MemoryRecord]] = []
        for record in self._records:
            if namespace and record.namespace != namespace:
                continue
            text = " ".join([record.key, str(record.value)]).lower()
            overlap = sum(1 for term in terms if term in text)
            if overlap:
                scored.append((overlap * record.score, record))
        scored.sort(key=lambda row: row[0], reverse=True)
        return [record for _, record in scored[:limit]]

    def all(self) -> list[MemoryRecord]:
        """Return all records."""
        return list(self._records)
