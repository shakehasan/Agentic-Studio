"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from .common import MarketingBaseModel, new_id, utc_now


class DashboardRole(StrEnum):
    """Role hierarchy for the dashboard command surface."""

    ADMIN = "admin"
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


ROLE_RANK: dict[DashboardRole, int] = {
    DashboardRole.VIEWER: 10,
    DashboardRole.REVIEWER: 20,
    DashboardRole.OPERATOR: 30,
    DashboardRole.ADMIN: 40,
}


class UserMemoryScope(StrEnum):
    """User-scoped memory tiers exposed to the dashboard."""

    SHORT = "short"
    LONG = "long"
    CHECKPOINT = "checkpoint"


class DashboardUser(MarketingBaseModel):
    """User who can operate or inspect the agent workforce."""

    id: str
    name: str
    role: DashboardRole
    title: str
    team: str = "Marketing"
    status: str = "active"
    avatar_hint: str = "user"
    created_at: object = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def can(self, required: DashboardRole) -> bool:
        """Return whether this user satisfies a required role."""
        return ROLE_RANK[self.role] >= ROLE_RANK[required]


class UserMemoryRecord(MarketingBaseModel):
    """Memory entry attached to a dashboard user."""

    id: str = Field(default_factory=lambda: new_id("umem"))
    user_id: str
    scope: UserMemoryScope
    key: str
    value: dict[str, Any]
    run_id: str | None = None
    created_by: str | None = None
    created_at: object = Field(default_factory=utc_now)


class DashboardCommandRequest(MarketingBaseModel):
    """Request to command the agent workforce for a selected user."""

    user_id: str
    brief: str = Field(min_length=8)
    workflow_type: str = "comprehensive_campaign"
    priority: int = Field(default=5, ge=1, le=10)
    channels: list[str] = Field(default_factory=list)
    approval_required: bool = False
    memory_notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DashboardWorkflowRecord(MarketingBaseModel):
    """Dashboard-facing record of an agent workflow command."""

    id: str = Field(default_factory=lambda: new_id("workflow"))
    run_id: str | None = None
    user_id: str
    requested_by: str
    brief: str
    workflow_type: str
    status: str
    priority: int = 5
    package_id: str | None = None
    summary: str = ""
    metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: object = Field(default_factory=utc_now)


class DashboardWorkflowResult(MarketingBaseModel):
    """Result returned to the web UI after an agent command."""

    workflow: DashboardWorkflowRecord
    memory: list[UserMemoryRecord] = Field(default_factory=list)
    artifact_markdown: str | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    approvals: list[dict[str, Any]] = Field(default_factory=list)

