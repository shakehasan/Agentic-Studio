"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(tz=UTC)


def new_id(prefix: str) -> str:
    """Create a short, stable-enough identifier for local records."""
    return f"{prefix}_{uuid4().hex[:12]}"


class RunStatus(StrEnum):
    """Lifecycle states for campaign execution."""

    PLANNED = "planned"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    REVISING = "revising"
    COMPLETED = "completed"
    FAILED = "failed"


class FailureKind(StrEnum):
    """Classify deterministic failures for orchestration decisions."""

    MODEL = "model_error"
    TOOL = "tool_error"
    POLICY = "policy_block"
    VALIDATION = "validation_error"
    INFRASTRUCTURE = "infrastructure_error"


class MarketingBaseModel(BaseModel):
    """Base model with strict validation and JSON-friendly defaults."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, arbitrary_types_allowed=True)


class Citation(MarketingBaseModel):
    """Citation to a local corpus source or generated artifact."""

    source_id: str
    title: str
    excerpt: str
    score: float = Field(ge=0, le=1)
    uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FailureStamp(MarketingBaseModel):
    """Structured failure marker used instead of ambiguous exceptions."""

    kind: FailureKind
    message: str
    retryable: bool = False
    component: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ConfidenceScore(MarketingBaseModel):
    """Confidence with a reason and optional calibration hints."""

    value: float = Field(ge=0, le=1)
    reason: str
    evidence: list[str] = Field(default_factory=list)

    @property
    def needs_review(self) -> bool:
        """Return whether confidence is below the human-review floor."""
        return self.value < 0.68
