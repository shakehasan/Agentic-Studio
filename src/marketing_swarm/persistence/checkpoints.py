"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from pathlib import Path

from marketing_swarm.schemas.state import GraphState


class SQLiteCheckpointer:
    """Durable checkpoint facade backed by the repository."""

    def __init__(self, path: str | Path = "data/marketing_swarm.sqlite3") -> None:
        from .repository import SQLiteRepository

        self.repository = SQLiteRepository(path)

    def save(self, state: GraphState) -> str:
        """Save a checkpoint and return its id."""
        self.repository.save_state(state)
        return f"checkpoint:{state.run_id}:{state.status.value}"

    def load(self, run_id: str) -> GraphState | None:
        """Load a checkpoint."""
        return self.repository.load_state(run_id)
