"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from .embeddings import HashingEmbeddingModel, cosine
from .types import Document, SearchResult


class InMemoryVectorStore:
    """Embedded vector store with deterministic local embeddings."""

    def __init__(self, embedding_model: HashingEmbeddingModel | None = None) -> None:
        self.embedding_model = embedding_model or HashingEmbeddingModel()
        self._documents: list[Document] = []
        self._vectors: dict[str, list[float]] = {}

    def add(self, documents: list[Document]) -> None:
        """Add documents and precompute vectors."""
        for document in documents:
            self._documents.append(document)
            self._vectors[document.id] = self.embedding_model.embed(document.text)

    def search(self, query: str, limit: int = 8) -> list[SearchResult]:
        """Return vector search results."""
        query_vector = self.embedding_model.embed(query)
        scored = []
        for document in self._documents:
            score = max(0.0, cosine(query_vector, self._vectors.get(document.id, [])))
            scored.append(SearchResult(document=document, score=score, reason="hashing vector similarity"))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]

    def all_documents(self) -> list[Document]:
        """Return all stored documents."""
        return list(self._documents)
