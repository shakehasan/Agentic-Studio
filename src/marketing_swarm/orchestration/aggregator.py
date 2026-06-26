"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from marketing_swarm.schemas.artifacts import AgentResult, CampaignPackage
from marketing_swarm.schemas.brief import CampaignBrief, RouteDecision


class CampaignAggregator:
    """Fan-in aggregator that assembles the final campaign package."""

    def assemble(self, run_id: str, brief: CampaignBrief, route: RouteDecision, results: dict[str, AgentResult]) -> CampaignPackage:
        """Assemble a holistic package."""
        assets = []
        confidence_values = []
        for agent in route.ordered_agents:
            result = results.get(agent)
            if result:
                assets.extend(result.assets)
                confidence_values.append(result.confidence.value)
        average_confidence = sum(confidence_values) / max(1, len(confidence_values))
        summary = (
            "This campaign package combines strategy, research, content, copy, search, lifecycle, creative, "
            "quality assurance, and optimization workstreams into a local-first execution plan."
        )
        return CampaignPackage(
            run_id=run_id,
            brief=brief.brief,
            strategy_summary=summary,
            assets=assets,
            routing_summary={
                "mode": route.mode,
                "reason": route.reason,
                "confidence": route.confidence,
                "agents": ", ".join(route.ordered_agents),
            },
            quality_summary={
                "average_agent_confidence": round(average_confidence, 3),
                "asset_count": len(assets),
                "qa_gate": "pass" if average_confidence >= 0.68 else "review",
            },
            metrics={"agent_count": len(results), "confidence_values": confidence_values},
        )
