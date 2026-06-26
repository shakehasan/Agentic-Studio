"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from typing import Any, Literal, Protocol, TypedDict

from langgraph.graph import END, StateGraph

from marketing_swarm.schemas.brief import CampaignBrief
from marketing_swarm.schemas.common import RunStatus
from marketing_swarm.schemas.state import GraphState


class CampaignGraphState(TypedDict, total=False):
    """Shared LangGraph state for one campaign execution."""

    brief: CampaignBrief | str
    state: GraphState


class CampaignGraphRuntime(Protocol):
    """Runtime methods required by the LangGraph campaign graph."""

    async def graph_prepare(self, graph_state: CampaignGraphState) -> dict[str, GraphState]:
        """Normalize the incoming brief and create initial run state."""

    async def graph_guardrails(self, graph_state: CampaignGraphState) -> dict[str, GraphState]:
        """Apply policy guardrails before planning."""

    async def graph_plan(self, graph_state: CampaignGraphState) -> dict[str, GraphState]:
        """Build and persist the route plan."""

    async def graph_execute(self, graph_state: CampaignGraphState) -> dict[str, GraphState]:
        """Dispatch agent tasks."""

    async def graph_aggregate(self, graph_state: CampaignGraphState) -> dict[str, GraphState]:
        """Assemble and persist the final campaign package."""


def _after_guardrails(graph_state: CampaignGraphState) -> Literal["plan", "__end__"]:
    """Route away from planning if guardrails failed."""
    state = graph_state["state"]
    return END if state.status == RunStatus.FAILED else "plan"


def _after_plan(graph_state: CampaignGraphState) -> Literal["execute", "__end__"]:
    """Route to execution unless planning paused for approval."""
    state = graph_state["state"]
    return END if state.status in {RunStatus.AWAITING_APPROVAL, RunStatus.FAILED} else "execute"


def _after_execute(graph_state: CampaignGraphState) -> Literal["aggregate", "__end__"]:
    """Route to aggregation unless execution paused for approval."""
    state = graph_state["state"]
    return END if state.status in {RunStatus.AWAITING_APPROVAL, RunStatus.FAILED} else "aggregate"


class CompiledCampaignGraph:
    """LangGraph-backed campaign graph runtime."""

    def __init__(self, runtime: CampaignGraphRuntime) -> None:
        builder = StateGraph(CampaignGraphState)
        builder.add_node("prepare", runtime.graph_prepare)
        builder.add_node("guardrails", runtime.graph_guardrails)
        builder.add_node("plan", runtime.graph_plan)
        builder.add_node("execute", runtime.graph_execute)
        builder.add_node("aggregate", runtime.graph_aggregate)
        builder.set_entry_point("prepare")
        builder.add_edge("prepare", "guardrails")
        builder.add_conditional_edges("guardrails", _after_guardrails, {"plan": "plan", END: END})
        builder.add_conditional_edges("plan", _after_plan, {"execute": "execute", END: END})
        builder.add_conditional_edges("execute", _after_execute, {"aggregate": "aggregate", END: END})
        builder.add_edge("aggregate", END)
        self.compiled = builder.compile(name="agentic-marketing-swarm")

    async def ainvoke(self, brief: CampaignBrief | str) -> GraphState:
        """Invoke the compiled LangGraph campaign graph asynchronously."""
        result: dict[str, Any] = await self.compiled.ainvoke({"brief": brief})
        return result["state"]


def build_graph(runtime: CampaignGraphRuntime) -> CompiledCampaignGraph:
    """Build the LangGraph campaign graph."""
    return CompiledCampaignGraph(runtime)
