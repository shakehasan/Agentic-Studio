"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from marketing_swarm.schemas.knowledge import KnowledgeChunk, KnowledgeSource


@dataclass(frozen=True, slots=True)
class ChunkingConfig:
    """Configuration for deterministic local text chunking."""

    target_tokens: int = 220
    overlap_tokens: int = 36
    min_tokens: int = 32
    preserve_headings: bool = True

    def validate(self) -> None:
        """Validate chunking settings."""
        if self.target_tokens < 40:
            raise ValueError("target_tokens must be at least 40")
        if self.overlap_tokens < 0:
            raise ValueError("overlap_tokens cannot be negative")
        if self.overlap_tokens >= self.target_tokens:
            raise ValueError("overlap_tokens must be smaller than target_tokens")
        if self.min_tokens < 1:
            raise ValueError("min_tokens must be positive")


class TextChunker:
    """Deterministic chunker that respects paragraphs and markdown headings."""

    def __init__(self, config: ChunkingConfig | None = None) -> None:
        self.config = config or ChunkingConfig()
        self.config.validate()

    def chunk_source(self, source: KnowledgeSource) -> list[KnowledgeChunk]:
        """Split a source into retrieval chunks."""
        blocks = self._blocks(source.text)
        windows = self._window_blocks(blocks)
        chunks: list[KnowledgeChunk] = []
        for ordinal, window in enumerate(windows):
            text = self._clean("\n\n".join(window))
            tokens = self._tokens(text)
            if len(tokens) < self.config.min_tokens and chunks:
                previous = chunks[-1]
                merged = self._clean(previous.text + "\n\n" + text)
                chunks[-1] = previous.model_copy(update={"text": merged, "token_count": len(self._tokens(merged))})
                continue
            chunks.append(
                KnowledgeChunk(
                    id=self._chunk_id(source, ordinal, text),
                    source_id=source.id,
                    namespace=source.namespace,
                    title=source.title,
                    uri=source.uri,
                    ordinal=ordinal,
                    text=text,
                    token_count=max(1, len(tokens)),
                    metadata={
                        "source_kind": source.kind.value,
                        "chunking": {
                            "target_tokens": self.config.target_tokens,
                            "overlap_tokens": self.config.overlap_tokens,
                        },
                    },
                )
            )
        return chunks

    def _blocks(self, text: str) -> list[str]:
        """Split text into meaningful blocks."""
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        raw_blocks = [block.strip() for block in re.split(r"\n{2,}", normalized) if block.strip()]
        if not raw_blocks:
            raw_blocks = [normalized.strip()]
        blocks: list[str] = []
        for block in raw_blocks:
            if self.config.preserve_headings and block.startswith("#"):
                blocks.append(block)
                continue
            sentences = self._sentence_split(block)
            current: list[str] = []
            for sentence in sentences:
                current.append(sentence)
                if len(self._tokens(" ".join(current))) >= self.config.target_tokens:
                    blocks.append(" ".join(current))
                    current = []
            if current:
                blocks.append(" ".join(current))
        return blocks

    def _window_blocks(self, blocks: list[str]) -> list[list[str]]:
        """Create overlapping token windows from text blocks."""
        windows: list[list[str]] = []
        current: list[str] = []
        current_tokens = 0
        for block in blocks:
            block_tokens = len(self._tokens(block))
            if current and current_tokens + block_tokens > self.config.target_tokens:
                windows.append(current)
                current = self._overlap_tail(current)
                current_tokens = len(self._tokens("\n\n".join(current)))
            current.append(block)
            current_tokens += block_tokens
        if current:
            windows.append(current)
        return windows

    def _overlap_tail(self, blocks: list[str]) -> list[str]:
        """Return the trailing blocks that fit inside the overlap budget."""
        if self.config.overlap_tokens == 0:
            return []
        tail: list[str] = []
        total = 0
        for block in reversed(blocks):
            count = len(self._tokens(block))
            if tail and total + count > self.config.overlap_tokens:
                break
            tail.insert(0, block)
            total += count
            if total >= self.config.overlap_tokens:
                break
        return tail

    def _sentence_split(self, text: str) -> list[str]:
        """Split text into sentence-like units without external NLP dependencies."""
        parts = re.split(r"(?<=[.!?])\s+", text.strip())
        return [part.strip() for part in parts if part.strip()]

    def _tokens(self, text: str) -> list[str]:
        """Return approximate tokens."""
        return re.findall(r"[A-Za-z0-9][A-Za-z0-9'_-]*", text)

    def _clean(self, text: str) -> str:
        """Normalize chunk text."""
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _chunk_id(self, source: KnowledgeSource, ordinal: int, text: str) -> str:
        """Create a stable chunk id."""
        digest = hashlib.sha256(f"{source.id}:{ordinal}:{text[:512]}".encode()).hexdigest()[:16]
        return f"kchunk_{digest}"

