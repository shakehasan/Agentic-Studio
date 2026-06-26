"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from .bm25 import tokenize
from .types import SearchResult


class CrossFeatureReranker:
    """Local cross-feature reranker using overlap, coverage, and title match."""

    def rerank(self, query: str, results: list[SearchResult], limit: int = 8) -> list[SearchResult]:
        """Rerank results deterministically."""
        q_terms = set(tokenize(query))
        reranked: list[SearchResult] = []
        for result in results:
            doc_terms = set(tokenize(result.document.text))
            title_terms = set(tokenize(result.document.title))
            overlap = len(q_terms & doc_terms) / max(1, len(q_terms))
            title_bonus = 0.1 if q_terms & title_terms else 0.0
            evidence_bonus = 0.05 if len(result.document.text) > 280 else 0.0
            score = min(1.0, 0.55 * result.score + 0.35 * overlap + title_bonus + evidence_bonus)
            reranked.append(
                SearchResult(document=result.document, score=score, reason=f"{result.reason}; reranked cross-feature")
            )
        reranked.sort(key=lambda item: item.score, reverse=True)
        return reranked[:limit]
