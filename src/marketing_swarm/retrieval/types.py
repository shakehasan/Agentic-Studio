"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field

from marketing_swarm.schemas.common import Citation, MarketingBaseModel, new_id


class Document(MarketingBaseModel):
    """A local knowledge-base document."""

    id: str = Field(default_factory=lambda: new_id("doc"))
    title: str
    text: str
    source: str = "local"
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_citation(self, score: float) -> Citation:
        """Create a citation from this document."""
        excerpt = self.text[:240].strip()
        return Citation(source_id=self.id, title=self.title, excerpt=excerpt, score=max(0.0, min(1.0, score)), uri=self.source)


class SearchResult(MarketingBaseModel):
    """Retrieved document with score and explanation."""

    document: Document
    score: float
    reason: str
