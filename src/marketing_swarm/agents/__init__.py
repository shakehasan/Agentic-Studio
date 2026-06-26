"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from .analytics_optimization import AnalyticsOptimizationAgent
from .brand_voice_qa import BrandVoiceQaAgent
from .competitive_intelligence import CompetitiveIntelligenceAgent
from .content_strategy import ContentStrategistAgent
from .copywriter import CopywriterAgent
from .creative_brief import CreativeBriefAgent
from .email_marketing import EmailMarketingAgent
from .market_research import MarketResearchAgent
from .seo_geo import SeoGeoAgent
from .social_media import SocialMediaAgent
from .supervisor import SupervisorAgent

AGENT_CLASSES = {
    "supervisor": SupervisorAgent,
    "market_research": MarketResearchAgent,
    "competitive_intelligence": CompetitiveIntelligenceAgent,
    "content_strategy": ContentStrategistAgent,
    "copywriter": CopywriterAgent,
    "seo_geo": SeoGeoAgent,
    "social_media": SocialMediaAgent,
    "email_marketing": EmailMarketingAgent,
    "creative_brief": CreativeBriefAgent,
    "brand_voice_qa": BrandVoiceQaAgent,
    "analytics_optimization": AnalyticsOptimizationAgent,
}


def create_agent(slug: str, **kwargs):
    """Create an agent by slug."""
    return AGENT_CLASSES[slug](**kwargs)
