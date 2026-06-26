"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator

from .common import MarketingBaseModel, new_id, utc_now


class CampaignBrief(MarketingBaseModel):
    """User brief normalized into a typed campaign request."""

    id: str = Field(default_factory=lambda: new_id("brief"))
    brief: str = Field(min_length=8)
    product: str | None = None
    audience: str | None = None
    region: str = "global"
    goals: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
    created_at: object = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("brief")
    @classmethod
    def clean_brief(cls, value: str) -> str:
        """Normalize whitespace and reject empty briefs."""
        cleaned = " ".join(value.split())
        if len(cleaned) < 8:
            raise ValueError("brief must contain a meaningful campaign request")
        return cleaned

    @classmethod
    def from_text(cls, text: str) -> CampaignBrief:
        """Create a brief from free text with conservative inferred defaults."""
        lower = text.lower()
        goals: list[str] = []
        for candidate in ["awareness", "activation", "conversion", "retention", "pipeline", "launch"]:
            if candidate in lower:
                goals.append(candidate)
        channels: list[str] = []
        for channel in ["email", "search", "social", "content", "webinar", "community"]:
            if channel in lower:
                channels.append(channel)
        audience = None
        if "for " in lower:
            audience = text[lower.rfind("for ") + 4 :].strip(" .")[:140] or None
        return cls(brief=text, goals=goals or ["awareness", "activation"], channels=channels, audience=audience)


class TaskSpec(MarketingBaseModel):
    """Single unit of work routed to a specialist agent."""

    id: str = Field(default_factory=lambda: new_id("task"))
    title: str
    description: str
    agent: str
    depends_on: list[str] = Field(default_factory=list)
    priority: int = Field(default=5, ge=1, le=10)
    required_tools: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RouteDecision(MarketingBaseModel):
    """Auditable routing decision made by the supervisor or router."""

    mode: str
    reason: str
    confidence: float = Field(ge=0, le=1)
    ordered_agents: list[str]
    parallel_groups: list[list[str]] = Field(default_factory=list)
    requires_human: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class CampaignPlan(MarketingBaseModel):
    """Executable graph plan for a campaign run."""

    id: str = Field(default_factory=lambda: new_id("plan"))
    brief_id: str
    route: RouteDecision
    tasks: list[TaskSpec]
    created_at: object = Field(default_factory=utc_now)

    def task_for_agent(self, agent: str) -> TaskSpec | None:
        """Return the first task assigned to an agent."""
        for task in self.tasks:
            if task.agent == agent:
                return task
        return None
