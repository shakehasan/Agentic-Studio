"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import Field

from marketing_swarm.retrieval.types import Document

from .common import MarketingBaseModel, new_id, utc_now


class KnowledgeSourceKind(StrEnum):
    """Supported local knowledge source formats."""

    MARKDOWN = "markdown"
    TEXT = "text"
    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"
    UNKNOWN = "unknown"


class KnowledgeSource(MarketingBaseModel):
    """Normalized local source document before chunking."""

    id: str = Field(default_factory=lambda: new_id("ksrc"))
    namespace: str = "default"
    title: str
    uri: str
    kind: KnowledgeSourceKind = KnowledgeSourceKind.UNKNOWN
    text: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: object = Field(default_factory=utc_now)

    @classmethod
    def from_path(
        cls,
        path: Path,
        text: str,
        *,
        namespace: str = "default",
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeSource:
        """Create a source from a filesystem path."""
        suffix = path.suffix.lower()
        kind = {
            ".md": KnowledgeSourceKind.MARKDOWN,
            ".markdown": KnowledgeSourceKind.MARKDOWN,
            ".txt": KnowledgeSourceKind.TEXT,
            ".json": KnowledgeSourceKind.JSON,
            ".jsonl": KnowledgeSourceKind.JSONL,
            ".csv": KnowledgeSourceKind.CSV,
        }.get(suffix, KnowledgeSourceKind.UNKNOWN)
        return cls(
            namespace=namespace,
            title=title or path.stem.replace("-", " ").replace("_", " ").title(),
            uri=str(path),
            kind=kind,
            text=text,
            metadata={"suffix": suffix, "bytes": path.stat().st_size, **(metadata or {})},
        )

    def to_document(self) -> Document:
        """Convert the source into a retrieval document."""
        return Document(id=self.id, title=self.title, text=self.text, source=self.uri, metadata=self.metadata)


class KnowledgeChunk(MarketingBaseModel):
    """Chunked source text ready for retrieval and citation."""

    id: str
    source_id: str
    namespace: str = "default"
    title: str
    uri: str
    ordinal: int = Field(ge=0)
    text: str = Field(min_length=1)
    token_count: int = Field(ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: object = Field(default_factory=utc_now)

    def to_document(self) -> Document:
        """Convert the chunk into a retrieval document."""
        return Document(
            id=self.id,
            title=f"{self.title} #{self.ordinal + 1}",
            text=self.text,
            source=self.uri,
            metadata={"source_id": self.source_id, "namespace": self.namespace, **self.metadata},
        )


class KnowledgeIngestionReport(MarketingBaseModel):
    """Summary of an ingestion run."""

    namespace: str
    source_count: int
    chunk_count: int
    skipped_count: int = 0
    errors: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    chunk_ids: list[str] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Return whether ingestion completed without errors."""
        return not self.errors and self.source_count > 0

    def to_markdown(self) -> str:
        """Render the report as operator-friendly markdown."""
        lines = [
            "| Field | Value |",
            "|---|---:|",
            f"| Namespace | {self.namespace} |",
            f"| Sources | {self.source_count} |",
            f"| Chunks | {self.chunk_count} |",
            f"| Skipped | {self.skipped_count} |",
            f"| Errors | {len(self.errors)} |",
        ]
        if self.errors:
            lines.extend(["", "## Errors", ""])
            lines.extend(f"- {error}" for error in self.errors)
        return "\n".join(lines)


class KnowledgeSearchHit(MarketingBaseModel):
    """Search result returned by the knowledge-base service."""

    id: str
    title: str
    source_id: str | None = None
    uri: str
    score: float = Field(ge=0, le=1)
    excerpt: str
    reason: str
    metadata: dict[str, Any] = Field(default_factory=dict)

