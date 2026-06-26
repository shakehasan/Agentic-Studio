"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from pathlib import Path

from marketing_swarm.persistence.repository import SQLiteRepository
from marketing_swarm.retrieval.pipeline import AgenticRAGPipeline
from marketing_swarm.schemas.knowledge import (
    KnowledgeChunk,
    KnowledgeIngestionReport,
    KnowledgeSearchHit,
    KnowledgeSource,
)

from .chunking import ChunkingConfig, TextChunker
from .loaders import LocalKnowledgeLoader


class KnowledgeBaseService:
    """High-level ingestion and search service for local campaign knowledge."""

    def __init__(
        self,
        repository: SQLiteRepository | None = None,
        loader: LocalKnowledgeLoader | None = None,
        chunker: TextChunker | None = None,
    ) -> None:
        self.repository = repository or SQLiteRepository()
        self.loader = loader or LocalKnowledgeLoader()
        self.chunker = chunker or TextChunker()
        self._memory_sources: list[KnowledgeSource] = []
        self._memory_chunks: list[KnowledgeChunk] = []

    @classmethod
    def with_chunking(
        cls,
        *,
        repository: SQLiteRepository | None = None,
        target_tokens: int = 220,
        overlap_tokens: int = 36,
    ) -> KnowledgeBaseService:
        """Create a service with explicit chunking settings."""
        return cls(
            repository=repository,
            chunker=TextChunker(ChunkingConfig(target_tokens=target_tokens, overlap_tokens=overlap_tokens)),
        )

    def ingest_path(
        self,
        path: Path | str,
        *,
        namespace: str = "default",
        recursive: bool = True,
        persist: bool = True,
    ) -> KnowledgeIngestionReport:
        """Load, chunk, and optionally persist local files."""
        errors: list[str] = []
        skipped_count = 0
        try:
            sources = self.loader.load_path(Path(path), namespace=namespace, recursive=recursive)
        except Exception as exc:
            return KnowledgeIngestionReport(namespace=namespace, source_count=0, chunk_count=0, errors=[str(exc)])

        chunks: list[KnowledgeChunk] = []
        accepted_sources: list[KnowledgeSource] = []
        for source in sources:
            try:
                source_chunks = self.chunker.chunk_source(source)
            except Exception as exc:
                errors.append(f"{source.uri}: {exc}")
                skipped_count += 1
                continue
            if not source_chunks:
                skipped_count += 1
                continue
            accepted_sources.append(source)
            chunks.extend(source_chunks)

        self._memory_sources.extend(accepted_sources)
        self._memory_chunks.extend(chunks)
        if persist and accepted_sources:
            self.repository.save_knowledge(accepted_sources, chunks)

        return KnowledgeIngestionReport(
            namespace=namespace,
            source_count=len(accepted_sources),
            chunk_count=len(chunks),
            skipped_count=skipped_count,
            errors=errors,
            source_ids=[source.id for source in accepted_sources],
            chunk_ids=[chunk.id for chunk in chunks],
        )

    def ingest_sources(
        self,
        sources: list[KnowledgeSource],
        *,
        persist: bool = True,
    ) -> KnowledgeIngestionReport:
        """Ingest already-normalized sources."""
        chunks: list[KnowledgeChunk] = []
        for source in sources:
            chunks.extend(self.chunker.chunk_source(source))
        self._memory_sources.extend(sources)
        self._memory_chunks.extend(chunks)
        if persist and sources:
            self.repository.save_knowledge(sources, chunks)
        namespace = sources[0].namespace if sources else "default"
        return KnowledgeIngestionReport(
            namespace=namespace,
            source_count=len(sources),
            chunk_count=len(chunks),
            source_ids=[source.id for source in sources],
            chunk_ids=[chunk.id for chunk in chunks],
        )

    def search(self, query: str, *, namespace: str | None = None, limit: int = 8) -> list[KnowledgeSearchHit]:
        """Search persisted and in-memory chunks with the agentic RAG pipeline."""
        chunks = self._load_chunks(namespace=namespace)
        if not chunks:
            return []
        documents = [chunk.to_document() for chunk in chunks]
        pipeline = AgenticRAGPipeline(documents=documents)
        results = pipeline.search(query, limit=limit)
        hits: list[KnowledgeSearchHit] = []
        for result in results:
            metadata = dict(result.document.metadata)
            hits.append(
                KnowledgeSearchHit(
                    id=result.document.id,
                    title=result.document.title,
                    source_id=metadata.get("source_id"),
                    uri=result.document.source,
                    score=round(result.score, 4),
                    excerpt=result.document.text[:360],
                    reason=result.reason,
                    metadata=metadata,
                )
            )
        return hits

    def list_sources(self, *, namespace: str | None = None, limit: int = 50) -> list[KnowledgeSource]:
        """List persisted sources and in-memory sources."""
        persisted = self.repository.list_knowledge_sources(namespace=namespace, limit=limit)
        if persisted:
            return persisted
        sources = self._memory_sources
        if namespace:
            sources = [source for source in sources if source.namespace == namespace]
        return sources[:limit]

    def manifest(self, *, namespace: str | None = None) -> dict[str, object]:
        """Return a compact index manifest for diagnostics."""
        sources = self.list_sources(namespace=namespace, limit=10_000)
        chunks = self._load_chunks(namespace=namespace)
        namespaces = sorted({source.namespace for source in sources} | {chunk.namespace for chunk in chunks})
        kinds: dict[str, int] = {}
        for source in sources:
            kinds[source.kind.value] = kinds.get(source.kind.value, 0) + 1
        return {
            "namespaces": namespaces,
            "source_count": len(sources),
            "chunk_count": len(chunks),
            "source_kinds": kinds,
            "sample_titles": [source.title for source in sources[:8]],
        }

    def _load_chunks(self, *, namespace: str | None = None) -> list[KnowledgeChunk]:
        """Load chunks from persistence, falling back to in-memory chunks."""
        chunks = self.repository.list_knowledge_chunks(namespace=namespace, limit=10_000)
        if chunks:
            return chunks
        if namespace:
            return [chunk for chunk in self._memory_chunks if chunk.namespace == namespace]
        return list(self._memory_chunks)

