"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from typing import Any

from marketing_swarm.schemas.artifacts import Asset
from marketing_swarm.schemas.brief import CampaignBrief, TaskSpec

from .base import AgentSpec, MarketingAgent


class BrandVoiceQaAgent(MarketingAgent):
    """Brand Voice & QA Agent: Verify tone, claims, consistency, compliance risks, and return pass or revise verdicts with targeted corrections."""

    def __init__(self, **kwargs: Any) -> None:
        spec = AgentSpec(
            slug="brand_voice_qa",
            display_name="Brand Voice & QA Agent",
            role="Verify tone, claims, consistency, compliance risks, and return pass or revise verdicts with targeted corrections.",
            allowed_tools=['claim_extractor', 'pii_redactor', 'artifact_validator', 'tone_sentiment_analyzer'],
            deliverables=['qa_verdict', 'claim_review', 'tone_review', 'revision_directives'],
            handoff_targets=['copywriter', 'content_strategy', 'seo_geo'],
            confidence_floor=0.72,
        )
        super().__init__(spec=spec, **kwargs)

    def build_prompt(self, brief: CampaignBrief, task: TaskSpec) -> str:
        """Build the task-specific instruction frame for this specialist."""
        context_lines = [
            "You are the Brand Voice & QA Agent.",
            "Operate as a senior marketing systems specialist in June 2026.",
            "Use only local evidence and explicitly mark assumptions.",
            "Return structured sections that can be merged into a campaign package.",
            f"Task: {task.title}",
            f"Brief: {brief.brief}",
            f"Audience: {brief.audience or 'derived from brief'}",
            f"Goals: {', '.join(brief.goals) if brief.goals else 'awareness, activation, retention'}",
        ]
        return "\n".join(context_lines)

    def synthesize_assets(
        self,
        brief: CampaignBrief,
        task: TaskSpec,
        tool_outputs: dict[str, Any],
        model_text: str,
    ) -> list[Asset]:
        """Create domain-specific assets from evidence, tool outputs, and generated text."""
        sections = self._standard_sections(brief, task, tool_outputs, model_text)
        sections.append(self._evidence_section(tool_outputs))
        sections.append(self._handoff_section(task))
        assets: list[Asset] = []
        for index, deliverable in enumerate(self.spec.deliverables, start=1):
            title = deliverable.replace("_", " ").title()
            content = self._render_markdown(
                heading=title,
                sections=sections,
                brief=brief,
                task=task,
                ordinal=index,
            )
            assets.append(
                Asset(
                    name=f"{self.spec.slug}_{deliverable}",
                    kind=deliverable,
                    title=title,
                    body=content,
                    metadata={
                        "agent": self.spec.slug,
                        "tool_count": len(tool_outputs),
                        "handoff_targets": list(self.spec.handoff_targets),
                        "revision_ready": self.spec.slug == "brand_voice_qa",
                    },
                )
            )
        return assets
