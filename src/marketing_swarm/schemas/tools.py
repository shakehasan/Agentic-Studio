"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field

from .common import FailureStamp, MarketingBaseModel, new_id, utc_now


class ToolRequest(MarketingBaseModel):
    """A validated tool invocation."""

    id: str = Field(default_factory=lambda: new_id("toolreq"))
    tool: str
    payload: dict[str, Any]
    run_id: str | None = None
    agent: str | None = None
    created_at: object = Field(default_factory=utc_now)


class ToolResult(MarketingBaseModel):
    """Structured tool result that never hides failures."""

    id: str = Field(default_factory=lambda: new_id("toolres"))
    tool: str
    ok: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: FailureStamp | None = None
    elapsed_ms: float = 0.0
    created_at: object = Field(default_factory=utc_now)
