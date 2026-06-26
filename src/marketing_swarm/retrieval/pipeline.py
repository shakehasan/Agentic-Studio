"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from marketing_swarm.playbooks.content_playbooks import search_content_playbooks_library
from marketing_swarm.playbooks.experiment_playbooks import search_experiment_playbooks_library
from marketing_swarm.playbooks.persona_playbooks import search_persona_playbooks_library

from .bm25 import BM25Index
from .reranker import CrossFeatureReranker
from .rrf import reciprocal_rank_fusion
from .types import Document, SearchResult
from .vector_store import InMemoryVectorStore


def default_documents() -> list[Document]:
    """Seed the local knowledge base from embedded playbooks."""
    docs: list[Document] = []
    for searcher, label in [
        (search_content_playbooks_library, "content"),
        (search_experiment_playbooks_library, "experiment"),
        (search_persona_playbooks_library, "persona"),
    ]:
        for item in searcher("campaign audience measurement content proof", limit=30):
            text = " ".join(str(value) for value in item.values())
            docs.append(Document(title=f"{label.title()} {item['id']}", text=text, source=f"playbook:{item['id']}"))
    return docs


class AgenticRAGPipeline:
    """Agentic RAG pipeline: rewrite, hybrid retrieval, RRF, rerank, cite."""

    def __init__(self, documents: list[Document] | None = None) -> None:
        self.vector_store = InMemoryVectorStore()
        self.bm25 = BM25Index()
        self.reranker = CrossFeatureReranker()
        seed = documents or default_documents()
        self.vector_store.add(seed)
        self.bm25.add(seed)

    def rewrite_query(self, query: str, context: str = "") -> list[str]:
        """Rewrite a query into specialist retrieval variants."""
        base = " ".join(query.split())
        variants = [
            base,
            f"{base} audience persona pain proof",
            f"{base} campaign channel measurement",
        ]
        if context:
            variants.append(f"{base} {context[:120]}")
        return list(dict.fromkeys(variants))

    def search(self, query: str, context: str = "", limit: int = 8) -> list[SearchResult]:
        """Run hybrid retrieval and rerank results."""
        fused_sets: list[list[SearchResult]] = []
        for rewritten in self.rewrite_query(query, context):
            dense = self.vector_store.search(rewritten, limit=limit)
            lexical = self.bm25.search(rewritten, limit=limit)
            fused_sets.append(reciprocal_rank_fusion([dense, lexical], limit=limit))
        fused = reciprocal_rank_fusion(fused_sets, limit=limit * 2)
        return self.reranker.rerank(query, fused, limit=limit)
