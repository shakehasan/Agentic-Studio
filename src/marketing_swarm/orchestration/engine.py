"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import asyncio
from typing import Any

from marketing_swarm.agents import create_agent
from marketing_swarm.config.settings import Settings
from marketing_swarm.guardrails.injection import injection_risk
from marketing_swarm.guardrails.pii import redact_pii
from marketing_swarm.llm.gateway import LLMGateway
from marketing_swarm.memory.manager import MemoryManager
from marketing_swarm.observability.metrics import MetricsRegistry
from marketing_swarm.observability.tracing import TraceRecorder
from marketing_swarm.persistence.repository import SQLiteRepository
from marketing_swarm.retrieval.pipeline import AgenticRAGPipeline
from marketing_swarm.schemas.brief import CampaignBrief
from marketing_swarm.schemas.common import FailureKind, FailureStamp, RunStatus
from marketing_swarm.schemas.handoff import HumanApprovalRequest
from marketing_swarm.schemas.state import GraphState
from marketing_swarm.tools.registry import build_default_registry

from .aggregator import CampaignAggregator
from .policies import QualityPolicy
from .router import MultiRouteRouter


class CampaignEngine:
    """End-to-end supervisor/orchestration engine with checkpointed execution."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.settings.ensure_dirs()
        self.metrics = MetricsRegistry()
        self.traces = TraceRecorder(self.settings.trace_path)
        self.llm = LLMGateway(self.settings, metrics=self.metrics)
        self.tools = build_default_registry()
        self.router = MultiRouteRouter()
        self.policy = QualityPolicy(self.settings.confidence_threshold, self.settings.qa_revision_limit)
        self.aggregator = CampaignAggregator()
        self.repository = SQLiteRepository(self.settings.db_path)
        self.memory = MemoryManager()
        self.rag = AgenticRAGPipeline()

    async def run(self, brief: CampaignBrief | str) -> GraphState:
        """Run a campaign to completion or HITL pause."""
        normalized = CampaignBrief.from_text(brief) if isinstance(brief, str) else brief
        redacted, count = redact_pii(normalized.brief)
        if count:
            normalized = normalized.model_copy(update={"brief": redacted, "metadata": {**normalized.metadata, "pii_redactions": count}})
        state = GraphState(brief=normalized)
        self.repository.save_state(state)
        risk = injection_risk(normalized.brief)
        if risk["blocked"]:
            state.failures.append(
                FailureStamp(
                    kind=FailureKind.POLICY,
                    message="prompt-injection risk detected",
                    retryable=False,
                    component="guardrails",
                    details=risk,
                )
            )
            state.mark(RunStatus.FAILED)
            self.repository.save_state(state)
            return state

        with self.traces.span("supervisor.plan", run_id=state.run_id):
            plan = self.router.build_plan(normalized)
            state.plan = plan
            state.add_route(plan.route)
            state.mark(RunStatus.DISPATCHED)
            self.repository.record_event(state.run_id, "route_decision", plan.route.model_dump(mode="json"))
            self.repository.save_state(state)

        if plan.route.requires_human:
            request = HumanApprovalRequest(
                run_id=state.run_id,
                reason="low route confidence",
                checkpoint_id=f"checkpoint:{state.run_id}:planned",
                summary=plan.route.reason,
            )
            state.approvals.append(request)
            state.mark(RunStatus.AWAITING_APPROVAL)
            self.repository.save_state(state)
            return state

        state.mark(RunStatus.RUNNING)
        documents = [result.document.model_dump() for result in self.rag.search(normalized.brief, limit=10)]
        context: dict[str, Any] = {"run_id": state.run_id, "documents": documents, "memory": self.memory.retrieve_context(normalized.brief)}

        completed: set[str] = set()
        for group in plan.route.parallel_groups:
            runnable = [task for task in plan.tasks if task.agent in group and task.agent not in completed]
            if runnable:
                await self._run_parallel(state, runnable, context)
                completed.update(task.agent for task in runnable)

        for task in plan.tasks:
            if task.agent in completed:
                continue
            await self._run_one(state, task, context)
            completed.add(task.agent)
            if state.status == RunStatus.AWAITING_APPROVAL:
                self.repository.save_state(state)
                return state

        qa_result = state.results.get("brand_voice_qa")
        if qa_result and self.policy.qa_verdict(qa_result) == "revise":
            await self._bounded_revision_loop(state, context)

        with self.traces.span("aggregator.package", run_id=state.run_id):
            state.package = self.aggregator.assemble(state.run_id, state.brief, plan.route, state.results)
            state.metrics = {**state.metrics, **self.metrics.snapshot(), "memory": self.memory.summarize()}
            state.mark(RunStatus.COMPLETED)
            self.repository.save_package(state.package)
            self.repository.save_state(state)
        return state

    async def _run_parallel(self, state: GraphState, tasks, context: dict[str, Any]) -> None:
        """Run independent tasks concurrently."""
        results = await asyncio.gather(*(self._agent_result(task, state.brief, context) for task in tasks))
        for result in results:
            state.add_result(result)
            self.repository.record_event(state.run_id, "agent_result", result.model_dump(mode="json"))

    async def _run_one(self, state: GraphState, task, context: dict[str, Any]) -> None:
        """Run one task with quality policy checks."""
        result = await self._agent_result(task, state.brief, context)
        state.add_result(result)
        self.repository.record_event(state.run_id, "agent_result", result.model_dump(mode="json"))
        if self.policy.requires_human(result):
            request = HumanApprovalRequest(
                run_id=state.run_id,
                reason=f"{result.agent} confidence below threshold",
                checkpoint_id=f"checkpoint:{state.run_id}:{result.agent}",
                summary=result.critique,
            )
            state.approvals.append(request)
            state.mark(RunStatus.AWAITING_APPROVAL)

    async def _agent_result(self, task, brief: CampaignBrief, context: dict[str, Any]):
        """Execute an agent inside a trace span."""
        with self.traces.span("agent.run", agent=task.agent, task_id=task.id):
            agent = create_agent(task.agent, llm=self.llm, tools=self.tools)
            return await agent.run(brief, task, context)

    async def _bounded_revision_loop(self, state: GraphState, context: dict[str, Any]) -> None:
        """Bounded QA loop that sends work back upstream."""
        if not state.plan:
            return
        state.mark(RunStatus.REVISING)
        targets = ["copywriter", "content_strategy", "seo_geo"]
        for attempt in range(self.settings.qa_revision_limit):
            for target in targets:
                task = state.plan.task_for_agent(target)
                if task is not None:
                    revised = await self._agent_result(task, state.brief, {**context, "revision_attempt": attempt + 1})
                    state.add_result(revised)
            qa_task = state.plan.task_for_agent("brand_voice_qa")
            if qa_task is not None:
                qa = await self._agent_result(qa_task, state.brief, {**context, "revision_attempt": attempt + 1})
                state.add_result(qa)
                if self.policy.qa_verdict(qa) == "pass":
                    return


def run_campaign_sync(brief: str) -> GraphState:
    """Convenience synchronous campaign runner."""
    return asyncio.run(CampaignEngine().run(brief))
