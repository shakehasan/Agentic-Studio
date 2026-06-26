"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from typing import Any

from .engine import CampaignEngine


class CompiledCampaignGraph:
    """Small adapter mirroring a compiled graph runtime."""

    def __init__(self, engine: CampaignEngine | None = None) -> None:
        self.engine = engine or CampaignEngine()

    async def ainvoke(self, brief: str) -> Any:
        """Invoke the campaign graph asynchronously."""
        return await self.engine.run(brief)


def build_graph(engine: CampaignEngine | None = None) -> CompiledCampaignGraph:
    """Build the campaign graph.

    The runtime is intentionally wrapped so optional graph libraries can be
    swapped in without changing API, CLI, or eval callers.
    """
    return CompiledCampaignGraph(engine)
