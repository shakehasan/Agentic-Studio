"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from typing import Any

from marketing_swarm.playbooks.content_playbooks import get_content_playbooks_library
from marketing_swarm.playbooks.experiment_playbooks import get_experiment_playbooks_library
from marketing_swarm.playbooks.persona_playbooks import get_persona_playbooks_library

from .episodic import EpisodicMemory
from .procedural import ProceduralMemory
from .semantic import SemanticMemory
from .working import WorkingMemory


class MemoryManager:
    """Coordinates four tiers of campaign memory."""

    def __init__(self) -> None:
        self.working = WorkingMemory()
        self.semantic = SemanticMemory()
        self.episodic = EpisodicMemory()
        self.procedural = ProceduralMemory()
        self._seed_procedural()

    def _seed_procedural(self) -> None:
        """Seed procedural memory from local playbook libraries."""
        for library_name, library in [
            ("content", get_content_playbooks_library()),
            ("experiment", get_experiment_playbooks_library()),
            ("persona", get_persona_playbooks_library()),
        ]:
            for key, value in list(library.items())[:80]:
                self.procedural.put(key=key, value=value, namespace=library_name, score=0.9)

    def remember_run_context(self, run_id: str, value: dict[str, Any]) -> None:
        """Store working and episodic context for a run."""
        self.working.put(key=run_id, value=value, namespace="run", score=1.0)
        self.episodic.put(key=run_id, value=value, namespace="runs", score=0.8)

    def retrieve_context(self, query: str, limit: int = 8) -> dict[str, list[dict[str, Any]]]:
        """Retrieve context from all memory tiers."""
        return {
            "working": [record.value for record in self.working.search(query, limit=limit)],
            "semantic": [record.value for record in self.semantic.search(query, limit=limit)],
            "episodic": [record.value for record in self.episodic.search(query, limit=limit)],
            "procedural": [record.value for record in self.procedural.search(query, limit=limit)],
        }

    def summarize(self) -> dict[str, dict[str, object]]:
        """Return memory tier summaries."""
        return {
            "working": self.working.summarize(),
            "semantic": self.semantic.summarize(),
            "episodic": self.episodic.summarize(),
            "procedural": self.procedural.summarize(),
        }
