"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from marketing_swarm.schemas.artifacts import AgentResult


class QualityPolicy:
    """Quality gates and escalation policy."""

    def __init__(self, threshold: float = 0.68, revision_limit: int = 2) -> None:
        self.threshold = threshold
        self.revision_limit = revision_limit

    def requires_human(self, result: AgentResult) -> bool:
        """Return whether result should pause for human approval."""
        return result.confidence.value < self.threshold or bool(result.failures)

    def qa_verdict(self, result: AgentResult) -> str:
        """Infer QA verdict from assets and confidence."""
        text = " ".join(asset.body.lower() for asset in result.assets)
        if result.confidence.value < self.threshold:
            return "revise"
        if "missing" in text or "unverified" in text:
            return "revise"
        return "pass"
