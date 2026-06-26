"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field

from .common import MarketingBaseModel, new_id


class HandoffSignal(MarketingBaseModel):
    """Typed agent-to-agent handoff payload."""

    id: str = Field(default_factory=lambda: new_id("handoff"))
    source_agent: str
    target_agent: str
    reason: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    requires_ack: bool = True


class HumanApprovalRequest(MarketingBaseModel):
    """Human-in-the-loop pause request."""

    id: str = Field(default_factory=lambda: new_id("approval"))
    run_id: str
    reason: str
    checkpoint_id: str
    summary: str
    options: list[str] = Field(default_factory=lambda: ["approve", "revise", "cancel"])
    metadata: dict[str, Any] = Field(default_factory=dict)
