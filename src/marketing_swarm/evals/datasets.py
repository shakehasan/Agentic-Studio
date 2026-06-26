"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GoldenBrief:
    """Golden eval case."""

    brief: str
    expected_agents: tuple[str, ...]
    expected_mode: str


GOLDEN_BRIEFS = [
    GoldenBrief(
        "Launch a campaign for a privacy-first notes tool for remote knowledge workers.",
        ("market_research", "competitive_intelligence", "content_strategy", "copywriter", "seo_geo"),
        "parallel_fanout",
    ),
    GoldenBrief(
        "Create an email nurture sequence for trial users who have not activated.",
        ("market_research", "email_marketing", "brand_voice_qa"),
        "deterministic",
    ),
    GoldenBrief(
        "Build an SEO and answer-engine optimization plan for a workflow automation product.",
        ("market_research", "seo_geo", "content_strategy"),
        "deterministic",
    ),
]
