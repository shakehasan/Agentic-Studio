"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from marketing_swarm.config.routing_tables import parallel_groups_for_intent, route_for_intent
from marketing_swarm.schemas.brief import CampaignBrief, CampaignPlan, RouteDecision, TaskSpec


class MultiRouteRouter:
    """Chooses deterministic, semantic, parallel, HITL, and cyclic-ready routes."""

    def classify_intent(self, brief: CampaignBrief) -> tuple[str, float, str]:
        """Classify the campaign intent."""
        lower = brief.brief.lower()
        if any(term in lower for term in ["launch", "go-to-market", "campaign"]):
            return "launch", 0.9, "launch signal detected"
        if "email" in lower or "lifecycle" in lower:
            return "email", 0.84, "email lifecycle signal detected"
        if "seo" in lower or "search" in lower or "answer engine" in lower:
            return "seo", 0.82, "search growth signal detected"
        if "social" in lower or "thread" in lower:
            return "social", 0.8, "social distribution signal detected"
        if "content" in lower or "editorial" in lower:
            return "content", 0.78, "content strategy signal detected"
        return "launch", 0.64, "semantic fallback for ambiguous brief"

    def build_plan(self, brief: CampaignBrief) -> CampaignPlan:
        """Build an auditable campaign plan."""
        intent, confidence, reason = self.classify_intent(brief)
        agents = route_for_intent(intent)
        mode = "deterministic" if confidence >= 0.78 else "semantic"
        if intent == "launch":
            mode = "parallel_fanout"
        route = RouteDecision(
            mode=mode,
            reason=reason,
            confidence=confidence,
            ordered_agents=agents,
            parallel_groups=parallel_groups_for_intent(intent),
            requires_human=confidence < 0.68,
            metadata={"intent": intent, "qa_loop": True, "hitl_threshold": 0.68},
        )
        tasks = [
            TaskSpec(
                title=f"{agent.replace('_', ' ').title()} workstream",
                description=f"Produce {agent.replace('_', ' ')} deliverables for: {brief.brief}",
                agent=agent,
                depends_on=[] if index < 2 else [agents[index - 1]],
                priority=max(1, 10 - index),
            )
            for index, agent in enumerate(agents)
        ]
        return CampaignPlan(brief_id=brief.id, route=route, tasks=tasks)
