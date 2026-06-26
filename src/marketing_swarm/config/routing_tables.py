"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

DETERMINISTIC_ROUTES: dict[str, list[str]] = {
    "launch": [
        "market_research",
        "competitive_intelligence",
        "content_strategy",
        "copywriter",
        "seo_geo",
        "social_media",
        "email_marketing",
        "creative_brief",
        "brand_voice_qa",
        "analytics_optimization",
    ],
    "content": ["content_strategy", "copywriter", "seo_geo", "brand_voice_qa", "analytics_optimization"],
    "email": ["market_research", "email_marketing", "brand_voice_qa", "analytics_optimization"],
    "seo": ["market_research", "seo_geo", "content_strategy", "brand_voice_qa", "analytics_optimization"],
    "social": ["market_research", "social_media", "copywriter", "brand_voice_qa", "analytics_optimization"],
}

PARALLEL_GROUPS: dict[str, list[list[str]]] = {
    "launch": [["market_research", "competitive_intelligence"], ["social_media", "email_marketing", "creative_brief"]],
    "content": [["content_strategy", "seo_geo"]],
    "email": [["market_research"], ["email_marketing"]],
    "seo": [["market_research", "competitive_intelligence"]],
    "social": [["market_research", "competitive_intelligence"], ["social_media", "copywriter"]],
}


def route_for_intent(intent: str) -> list[str]:
    """Return a deterministic route for a normalized intent."""
    return list(DETERMINISTIC_ROUTES.get(intent, DETERMINISTIC_ROUTES["launch"]))


def parallel_groups_for_intent(intent: str) -> list[list[str]]:
    """Return parallel fan-out groups for an intent."""
    return [list(group) for group in PARALLEL_GROUPS.get(intent, PARALLEL_GROUPS["launch"])]
