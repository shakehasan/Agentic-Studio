"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import hashlib
import math


class HashingEmbeddingModel:
    """Deterministic local embedding model based on feature hashing."""

    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        """Embed text into a normalized hashing vector."""
        vector = [0.0 for _ in range(self.dimensions)]
        tokens = [token.strip(".,:;!?()[]{}").lower() for token in text.split() if token.strip()]
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


def cosine(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for normalized vectors."""
    if not left or not right:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=False))
