"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from marketing_swarm.schemas.common import FailureKind, FailureStamp

DISALLOWED_CLAIM_MARKERS = ["guaranteed cure", "risk-free profit", "100% guaranteed outcome"]


def check_content_policy(text: str, component: str = "guardrails") -> FailureStamp | None:
    """Block deterministic high-risk marketing claims."""
    lower = text.lower()
    for marker in DISALLOWED_CLAIM_MARKERS:
        if marker in lower:
            return FailureStamp(
                kind=FailureKind.POLICY,
                message=f"disallowed claim marker: {marker}",
                retryable=False,
                component=component,
                details={"marker": marker},
            )
    return None
