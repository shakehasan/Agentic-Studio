"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from marketing_swarm.config.settings import Settings
from marketing_swarm.orchestration.engine import CampaignEngine

from .datasets import GOLDEN_BRIEFS
from .scorers import package_quality, routing_accuracy


@dataclass(slots=True)
class EvalReport:
    """Eval report with regression gate status."""

    routing_score: float
    quality_score: float
    cases: int
    passed: bool

    def to_markdown(self) -> str:
        """Render report markdown."""
        return (
            "| Metric | Score | Gate |\n"
            "|---|---:|---:|\n"
            f"| Routing accuracy | {self.routing_score:.3f} | 0.800 |\n"
            f"| Package quality | {self.quality_score:.3f} | 0.650 |\n"
            f"| Cases | {self.cases} | - |\n"
            f"| Passed | {self.passed} | true |"
        )


class EvalHarness:
    """Deterministic eval harness for CI."""

    def __init__(self, settings: Settings | None = None) -> None:
        base = Path("test_artifacts") / "evals" / uuid4().hex
        self.settings = settings or Settings(
            db_path=base / "eval.sqlite3",
            artifact_dir=base / "artifacts",
            trace_path=base / "traces.jsonl",
        )

    def run(self) -> EvalReport:
        """Run evals synchronously."""
        return asyncio.run(self.arun())

    async def arun(self) -> EvalReport:
        """Run evals asynchronously."""
        engine = CampaignEngine(self.settings)
        routing_scores = []
        quality_scores = []
        for case in GOLDEN_BRIEFS:
            state = await engine.run(case.brief)
            if not state.plan or not state.package:
                routing_scores.append(0.0)
                quality_scores.append(0.0)
                continue
            routing_scores.append(routing_accuracy(state.plan.route, case.expected_agents, case.expected_mode))
            quality_scores.append(package_quality(state.package))
        routing = sum(routing_scores) / max(1, len(routing_scores))
        quality = sum(quality_scores) / max(1, len(quality_scores))
        return EvalReport(
            routing_score=round(routing, 3),
            quality_score=round(quality, 3),
            cases=len(GOLDEN_BRIEFS),
            passed=routing >= 0.8 and quality >= 0.65,
        )
