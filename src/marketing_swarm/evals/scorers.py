"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from marketing_swarm.schemas.artifacts import CampaignPackage
from marketing_swarm.schemas.brief import RouteDecision


def routing_accuracy(route: RouteDecision, expected_agents: tuple[str, ...], expected_mode: str) -> float:
    """Score routing mode and expected agent inclusion."""
    agent_hits = sum(1 for agent in expected_agents if agent in route.ordered_agents) / max(1, len(expected_agents))
    mode_hit = 1.0 if route.mode == expected_mode or expected_mode in route.mode else 0.0
    return round(0.75 * agent_hits + 0.25 * mode_hit, 3)


def package_quality(package: CampaignPackage) -> float:
    """Deterministic quality proxy for package completeness."""
    asset_kinds = {asset.kind for asset in package.assets}
    body_words = sum(len(asset.body.split()) for asset in package.assets)
    breadth = min(1.0, len(asset_kinds) / 18)
    depth = min(1.0, body_words / 1800)
    qa = 1.0 if package.quality_summary.get("qa_gate") == "pass" else 0.55
    return round(0.4 * breadth + 0.4 * depth + 0.2 * qa, 3)


def guardrail_score(blocked: bool, should_block: bool) -> float:
    """Score guardrail efficacy."""
    return 1.0 if blocked == should_block else 0.0
