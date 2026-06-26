"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from .types import SearchResult


def reciprocal_rank_fusion(result_sets: list[list[SearchResult]], k: int = 60, limit: int = 10) -> list[SearchResult]:
    """Fuse ranked lists using reciprocal rank fusion."""
    scores: dict[str, float] = {}
    representatives: dict[str, SearchResult] = {}
    reasons: dict[str, list[str]] = {}
    for results in result_sets:
        for rank, result in enumerate(results, start=1):
            doc_id = result.document.id
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            representatives[doc_id] = result
            reasons.setdefault(doc_id, []).append(result.reason)
    fused: list[SearchResult] = []
    max_score = max(scores.values(), default=1.0)
    for doc_id, raw_score in scores.items():
        representative = representatives[doc_id]
        fused.append(
            SearchResult(
                document=representative.document,
                score=raw_score / max_score,
                reason=" + ".join(sorted(set(reasons[doc_id]))),
            )
        )
    fused.sort(key=lambda item: item.score, reverse=True)
    return fused[:limit]
