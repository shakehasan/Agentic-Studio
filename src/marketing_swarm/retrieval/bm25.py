"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from collections import Counter
from math import log

from .types import Document, SearchResult


def tokenize(text: str) -> list[str]:
    """Tokenize text for lexical retrieval."""
    return [token.strip(".,:;!?()[]{}").lower() for token in text.split() if len(token.strip(".,:;!?()[]{}")) > 2]


class BM25Index:
    """Small BM25 implementation used when optional packages are unavailable."""

    def __init__(self) -> None:
        self.documents: list[Document] = []
        self.term_freqs: list[Counter[str]] = []
        self.doc_freqs: Counter[str] = Counter()
        self.avgdl = 0.0

    def add(self, documents: list[Document]) -> None:
        """Index documents."""
        for document in documents:
            tokens = tokenize(document.text)
            counts = Counter(tokens)
            self.documents.append(document)
            self.term_freqs.append(counts)
            self.doc_freqs.update(set(tokens))
        total_length = sum(sum(counts.values()) for counts in self.term_freqs)
        self.avgdl = total_length / max(1, len(self.term_freqs))

    def search(self, query: str, limit: int = 8) -> list[SearchResult]:
        """Search the index."""
        q_tokens = tokenize(query)
        scored: list[SearchResult] = []
        total_docs = max(1, len(self.documents))
        for document, counts in zip(self.documents, self.term_freqs, strict=False):
            doc_len = sum(counts.values()) or 1
            score = 0.0
            for token in q_tokens:
                freq = counts[token]
                if not freq:
                    continue
                idf = log(1 + (total_docs - self.doc_freqs[token] + 0.5) / (self.doc_freqs[token] + 0.5))
                denom = freq + 1.5 * (1 - 0.75 + 0.75 * doc_len / max(1.0, self.avgdl))
                score += idf * (freq * 2.5) / denom
            normalized = score / (score + 4.0) if score > 0 else 0.0
            scored.append(SearchResult(document=document, score=normalized, reason="local bm25 lexical match"))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]
