"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from marketing_swarm.config.model_registry import get_model_profile
from marketing_swarm.llm.gateway import LLMGateway
from marketing_swarm.schemas.artifacts import AgentResult, Asset
from marketing_swarm.schemas.brief import CampaignBrief, TaskSpec
from marketing_swarm.schemas.common import ConfidenceScore
from marketing_swarm.tools.base import ToolContext
from marketing_swarm.tools.registry import ToolRegistry, build_default_registry


@dataclass(frozen=True, slots=True)
class AgentSpec:
    """Static configuration for a specialist agent."""

    slug: str
    display_name: str
    role: str
    allowed_tools: list[str]
    deliverables: list[str]
    handoff_targets: list[str]
    confidence_floor: float = 0.7


class MarketingAgent:
    """Base reasoning loop: plan, act, observe, critique, hand off."""

    def __init__(
        self,
        spec: AgentSpec,
        llm: LLMGateway | None = None,
        tools: ToolRegistry | None = None,
    ) -> None:
        self.spec = spec
        self.llm = llm or LLMGateway()
        self.tools = tools or build_default_registry()

    def build_prompt(self, brief: CampaignBrief, task: TaskSpec) -> str:
        """Build a default task prompt."""
        return f"{self.spec.display_name}: {self.spec.role}\nBrief: {brief.brief}\nTask: {task.description}"

    async def run(self, brief: CampaignBrief, task: TaskSpec, context: dict[str, Any] | None = None) -> AgentResult:
        """Execute the full specialist reasoning loop."""
        context = context or {}
        plan = self.plan(brief, task, context)
        tool_outputs = self.act(brief, task, plan, context)
        prompt = self.build_prompt(brief, task) + "\nTool observations:\n" + json.dumps(tool_outputs, default=str)[:6000]
        profile = get_model_profile(self.spec.slug)
        response = await self.llm.generate(
            prompt,
            model=profile.name,
            temperature=profile.temperature,
            json_mode=False,
            provider="fake" if profile.provider == "local" else profile.provider,
            metadata={"agent": self.spec.slug},
        )
        assets = self.synthesize_assets(brief, task, tool_outputs, response.text)
        critique = self.critique(brief, task, assets, tool_outputs)
        confidence = self.score_confidence(tool_outputs, assets, critique)
        return AgentResult(
            agent=self.spec.slug,
            task_id=task.id,
            confidence=confidence,
            assets=assets,
            critique=critique,
            handoff=self.handoff_payload(task, assets),
            metrics={
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "tool_count": len(tool_outputs),
                "allowed_tools": list(self.spec.allowed_tools),
            },
        )

    def plan(self, brief: CampaignBrief, task: TaskSpec, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Create a local tool plan."""
        query = f"{brief.brief} {task.description}"
        plan = []
        for tool in self.spec.allowed_tools:
            plan.append(
                {
                    "tool": tool,
                    "payload": {
                        "query": query,
                        "brief": brief.brief,
                        "limit": 5,
                        "channel": ",".join(brief.channels) if brief.channels else "owned",
                        "documents": context.get("documents", []),
                    },
                }
            )
        return plan

    def act(
        self,
        brief: CampaignBrief,
        task: TaskSpec,
        plan: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Run planned tools and collect observations."""
        outputs: dict[str, Any] = {}
        tool_context = ToolContext(run_id=context.get("run_id"), agent=self.spec.slug, knowledge_base=context.get("documents", []))
        for step in plan:
            result = self.tools.run(step["tool"], step["payload"], tool_context)
            outputs[step["tool"]] = result.model_dump(mode="json")
        return outputs

    def synthesize_assets(
        self,
        brief: CampaignBrief,
        task: TaskSpec,
        tool_outputs: dict[str, Any],
        model_text: str,
    ) -> list[Asset]:
        """Create generic assets."""
        body = self._render_markdown("Campaign Work", self._standard_sections(brief, task, tool_outputs, model_text), brief, task, 1)
        return [Asset(name=f"{self.spec.slug}_work", kind="work", title=self.spec.display_name, body=body)]

    def critique(self, brief: CampaignBrief, task: TaskSpec, assets: list[Asset], tool_outputs: dict[str, Any]) -> str:
        """Self-critique the output."""
        missing = [deliverable for deliverable in self.spec.deliverables if deliverable not in " ".join(a.name for a in assets)]
        evidence_count = sum(1 for value in tool_outputs.values() if value.get("ok"))
        if missing:
            return f"Review deliverable coverage for {', '.join(missing)}. Evidence tools succeeded: {evidence_count}."
        return f"Deliverables are covered with {evidence_count} local tool observations and bounded assumptions."

    def score_confidence(self, tool_outputs: dict[str, Any], assets: list[Asset], critique: str) -> ConfidenceScore:
        """Score confidence from tool success, artifact depth, and critique."""
        successes = sum(1 for value in tool_outputs.values() if value.get("ok"))
        tool_score = successes / max(1, len(tool_outputs))
        depth_score = min(1.0, sum(len(asset.body.split()) for asset in assets) / 360)
        value = max(0.0, min(0.97, 0.42 + 0.32 * tool_score + 0.2 * depth_score))
        if "Review" in critique:
            value -= 0.05
        return ConfidenceScore(value=round(value, 3), reason="tool success plus artifact depth", evidence=list(tool_outputs)[:8])

    def handoff_payload(self, task: TaskSpec, assets: list[Asset]) -> dict[str, Any]:
        """Create a typed handoff payload."""
        return {
            "source_agent": self.spec.slug,
            "targets": list(self.spec.handoff_targets),
            "task_id": task.id,
            "asset_ids": [asset.id for asset in assets],
            "summary": f"{self.spec.display_name} completed {len(assets)} assets.",
        }

    def _standard_sections(
        self,
        brief: CampaignBrief,
        task: TaskSpec,
        tool_outputs: dict[str, Any],
        model_text: str,
    ) -> list[dict[str, str]]:
        """Create reusable sections for assets."""
        observations = []
        for tool, result in tool_outputs.items():
            data = result.get("data", {})
            observations.append(f"{tool}: {data.get('summary', 'no summary')}")
        return [
            {"heading": "Audience", "body": brief.audience or "Audience inferred from the campaign brief and evidence."},
            {"heading": "Task", "body": task.description},
            {"heading": "Message", "body": model_text},
            {"heading": "Evidence", "body": "\n".join(f"- {item}" for item in observations[:8])},
            {"heading": "Action", "body": "Use this artifact in the campaign package and measure response before scaling."},
        ]

    def _evidence_section(self, tool_outputs: dict[str, Any]) -> dict[str, str]:
        """Render evidence section."""
        lines = []
        for name, result in tool_outputs.items():
            data = result.get("data", {})
            lines.append(f"- {name}: {data.get('summary', 'completed')}")
        return {"heading": "Local Evidence", "body": "\n".join(lines)}

    def _handoff_section(self, task: TaskSpec) -> dict[str, str]:
        """Render handoff section."""
        targets = ", ".join(self.spec.handoff_targets) if self.spec.handoff_targets else "supervisor"
        return {"heading": "Handoff", "body": f"Next consumers: {targets}. Task priority: {task.priority}."}

    def _render_markdown(
        self,
        heading: str,
        sections: list[dict[str, str]],
        brief: CampaignBrief,
        task: TaskSpec,
        ordinal: int,
    ) -> str:
        """Render asset markdown consistently."""
        lines = [
            f"### {heading}",
            "",
            f"**Campaign brief:** {brief.brief}",
            f"**Task:** {task.title}",
            f"**Artifact number:** {ordinal}",
            "",
        ]
        for section in sections:
            lines.append(f"#### {section['heading']}")
            lines.append("")
            lines.append(section["body"])
            lines.append("")
        return "\n".join(lines).strip()
