"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from typing import Any

from pydantic import Field

from .common import Citation, ConfidenceScore, FailureStamp, MarketingBaseModel, new_id, utc_now


class Asset(MarketingBaseModel):
    """A campaign artifact produced by an agent."""

    id: str = Field(default_factory=lambda: new_id("asset"))
    name: str
    kind: str
    title: str
    body: str
    citations: list[Citation] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: object = Field(default_factory=utc_now)

    def as_markdown(self) -> str:
        """Render the asset as standalone markdown."""
        citation_block = ""
        if self.citations:
            rows = [f"- {c.title}: {c.excerpt}" for c in self.citations]
            citation_block = "\n\n### Citations\n" + "\n".join(rows)
        return f"## {self.title}\n\n{self.body}{citation_block}\n"


class AgentResult(MarketingBaseModel):
    """Typed result from one specialist agent."""

    agent: str
    task_id: str
    confidence: ConfidenceScore
    assets: list[Asset]
    critique: str
    handoff: dict[str, Any] = Field(default_factory=dict)
    failures: list[FailureStamp] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Return whether the agent result is usable without mandatory review."""
        return not self.failures and not self.confidence.needs_review


class CampaignPackage(MarketingBaseModel):
    """Final package assembled from all specialist outputs."""

    id: str = Field(default_factory=lambda: new_id("package"))
    run_id: str
    brief: str
    strategy_summary: str
    assets: list[Asset]
    routing_summary: dict[str, Any]
    quality_summary: dict[str, Any]
    metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: object = Field(default_factory=utc_now)

    def to_markdown(self) -> str:
        """Render the complete package as markdown."""
        lines = [
            "# Campaign Package",
            "",
            self.strategy_summary,
            "",
            "## Routing Summary",
            "",
        ]
        for key, value in self.routing_summary.items():
            lines.append(f"- **{key}**: {value}")
        lines.extend(["", "## Quality Summary", ""])
        for key, value in self.quality_summary.items():
            lines.append(f"- **{key}**: {value}")
        lines.append("")
        for asset in self.assets:
            lines.append(asset.as_markdown())
        return "\n".join(lines)
