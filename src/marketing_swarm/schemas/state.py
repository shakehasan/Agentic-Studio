"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field

from .artifacts import AgentResult, CampaignPackage
from .brief import CampaignBrief, CampaignPlan, RouteDecision
from .common import FailureStamp, MarketingBaseModel, RunStatus, new_id, utc_now
from .handoff import HandoffSignal, HumanApprovalRequest


class GraphState(MarketingBaseModel):
    """Checkpointable campaign graph state."""

    run_id: str = Field(default_factory=lambda: new_id("run"))
    status: RunStatus = RunStatus.PLANNED
    brief: CampaignBrief
    plan: CampaignPlan | None = None
    route_history: list[RouteDecision] = Field(default_factory=list)
    results: dict[str, AgentResult] = Field(default_factory=dict)
    handoffs: list[HandoffSignal] = Field(default_factory=list)
    approvals: list[HumanApprovalRequest] = Field(default_factory=list)
    package: CampaignPackage | None = None
    failures: list[FailureStamp] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: object = Field(default_factory=utc_now)
    updated_at: object = Field(default_factory=utc_now)

    def mark(self, status: RunStatus) -> None:
        """Update run status and timestamp."""
        self.status = status
        self.updated_at = utc_now()

    def add_result(self, result: AgentResult) -> None:
        """Merge an agent result into state."""
        self.results[result.agent] = result
        self.updated_at = utc_now()

    def add_route(self, route: RouteDecision) -> None:
        """Append an auditable route decision."""
        self.route_history.append(route)
        self.updated_at = utc_now()
