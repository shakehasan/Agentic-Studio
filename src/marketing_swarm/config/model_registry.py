"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelProfile:
    """Per-agent model assignment profile."""

    name: str
    provider: str
    context_window: int
    temperature: float
    json_mode: bool = True
    cost_per_1k_tokens: float = 0.0


DEFAULT_MODEL_REGISTRY: dict[str, ModelProfile] = {
    "supervisor": ModelProfile("local-director", "local", 8192, 0.2),
    "market_research": ModelProfile("local-research", "local", 8192, 0.25),
    "competitive_intelligence": ModelProfile("local-analyst", "local", 8192, 0.25),
    "content_strategy": ModelProfile("local-strategy", "local", 8192, 0.35),
    "copywriter": ModelProfile("local-copy", "local", 8192, 0.55),
    "seo_geo": ModelProfile("local-search", "local", 8192, 0.25),
    "social_media": ModelProfile("local-social", "local", 8192, 0.6),
    "email_marketing": ModelProfile("local-lifecycle", "local", 8192, 0.45),
    "creative_brief": ModelProfile("local-creative", "local", 8192, 0.5),
    "brand_voice_qa": ModelProfile("local-qa", "local", 8192, 0.1),
    "analytics_optimization": ModelProfile("local-measurement", "local", 8192, 0.2),
}


def get_model_profile(agent: str) -> ModelProfile:
    """Return model profile for an agent, falling back to supervisor."""
    return DEFAULT_MODEL_REGISTRY.get(agent, DEFAULT_MODEL_REGISTRY["supervisor"])
