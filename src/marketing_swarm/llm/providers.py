"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx


@dataclass(slots=True)
class LLMRequest:
    """Provider-neutral model request."""

    prompt: str
    model: str
    temperature: float = 0.2
    json_mode: bool = False
    system: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LLMResponse:
    """Provider-neutral model response."""

    text: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(Protocol):
    """Minimal async provider protocol."""

    name: str

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response."""


def estimate_tokens(text: str) -> int:
    """Approximate tokens without requiring a tokenizer."""
    return max(1, len(text.split()) + len(text) // 16)


class FakeProvider:
    """Deterministic provider used for tests and offline demos."""

    name = "fake"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Return a structured local response without external calls."""
        await asyncio.sleep(0)
        keywords = [word.strip(".,:;!?").lower() for word in request.prompt.split() if len(word.strip(".,:;!?")) > 4]
        unique = list(dict.fromkeys(keywords))[:12]
        if request.json_mode:
            payload = {
                "summary": "Local deterministic synthesis generated from the campaign context.",
                "keywords": unique,
                "confidence": 0.79,
                "sections": [
                    {"title": "Core Insight", "body": "The brief implies a clear audience job, measurable goal, and multi-channel path."},
                    {"title": "Recommended Action", "body": "Use evidence-led messaging, gated quality checks, and staged optimization."},
                ],
            }
            text = json.dumps(payload)
        else:
            text = (
                "Local deterministic synthesis: "
                + ", ".join(unique[:8])
                + ". Prioritize clear positioning, proof, cadence, and measurable learning loops."
            )
        return LLMResponse(
            text=text,
            model=request.model,
            provider=self.name,
            input_tokens=estimate_tokens(request.prompt),
            output_tokens=estimate_tokens(text),
            metadata={"deterministic": True},
        )


class LocalProvider:
    """Provider for a locally hosted model runtime with a generic HTTP interface."""

    name = "local"

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint.rstrip("/")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Call the local model runtime and return a normalized response."""
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": False,
            "options": {"temperature": request.temperature},
        }
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(f"{self.endpoint}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
        text = str(data.get("response") or data.get("text") or "")
        return LLMResponse(
            text=text,
            model=request.model,
            provider=self.name,
            input_tokens=estimate_tokens(request.prompt),
            output_tokens=estimate_tokens(text),
            cost=0.0,
            metadata={"raw_keys": sorted(data.keys())},
        )
