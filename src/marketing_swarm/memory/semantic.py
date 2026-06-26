"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from .base import MemoryTier


class SemanticMemory(MemoryTier):
    """Vector-backed durable brand and campaign knowledge."""

    def __init__(self) -> None:
        super().__init__("semantic")

    def summarize(self) -> dict[str, object]:
        """Return tier summary for observability and debugging."""
        records = self.all()
        namespaces = sorted({record.namespace for record in records})
        return {"tier": self.name, "records": len(records), "namespaces": namespaces}
