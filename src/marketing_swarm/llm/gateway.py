"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import asyncio
import json
from collections.abc import Iterable
from typing import Any

from marketing_swarm.config.settings import Settings
from marketing_swarm.observability.metrics import MetricsRegistry

from .providers import FakeProvider, LLMProvider, LLMRequest, LLMResponse, LocalProvider


class LLMGateway:
    """Provider-agnostic gateway with fallback, retries, JSON mode, and token accounting."""

    def __init__(
        self,
        settings: Settings | None = None,
        providers: Iterable[LLMProvider] | None = None,
        metrics: MetricsRegistry | None = None,
    ) -> None:
        self.settings = settings or Settings.from_env()
        configured = list(providers or [])
        if not configured:
            configured.append(FakeProvider())
            if self.settings.llm_provider == "local":
                configured.insert(0, LocalProvider(self.settings.local_endpoint))
        self.providers = {provider.name: provider for provider in configured}
        self.fallback_chain = [self.settings.llm_provider, "fake"] if self.settings.llm_provider != "fake" else ["fake"]
        self.metrics = metrics or MetricsRegistry()

    async def generate(
        self,
        prompt: str,
        model: str,
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
        provider: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Generate text with retry and provider fallback."""
        request = LLMRequest(
            prompt=prompt,
            model=model,
            temperature=temperature,
            json_mode=json_mode,
            metadata=metadata or {},
        )
        chain = [provider] if provider else list(self.fallback_chain)
        errors: list[str] = []
        for provider_name in chain:
            if not provider_name:
                continue
            candidate = self.providers.get(provider_name)
            if candidate is None:
                errors.append(f"provider {provider_name} not configured")
                continue
            for attempt in range(3):
                try:
                    response = await candidate.generate(request)
                    self.metrics.increment("llm.calls", {"provider": response.provider, "model": response.model})
                    self.metrics.observe("llm.tokens.input", response.input_tokens, {"model": response.model})
                    self.metrics.observe("llm.tokens.output", response.output_tokens, {"model": response.model})
                    return response
                except Exception as exc:  # deterministic wrapping happens at the gateway boundary
                    errors.append(f"{provider_name} attempt {attempt + 1}: {exc}")
                    await asyncio.sleep(0.05 * (attempt + 1))
        raise RuntimeError("; ".join(errors) or "no provider available")

    async def generate_json(self, prompt: str, model: str, *, provider: str | None = None) -> dict[str, Any]:
        """Generate and parse a JSON object, repairing to a safe envelope on parse failure."""
        response = await self.generate(prompt, model, json_mode=True, provider=provider)
        try:
            data = json.loads(response.text)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        return {"summary": response.text, "confidence": 0.55, "sections": []}
