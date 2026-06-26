"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Settings:
    """Runtime settings with local-first defaults."""

    db_path: Path = Path("runtime/marketing_swarm.sqlite3")
    artifact_dir: Path = Path("runtime/artifacts")
    llm_provider: str = "fake"
    local_endpoint: str = "http://localhost:11434"
    default_model: str = "local-general"
    confidence_threshold: float = 0.68
    qa_revision_limit: int = 2
    trace_path: Path = Path("runtime/traces.jsonl")
    log_level: str = "INFO"
    extra: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> Settings:
        """Load settings from environment variables."""
        return cls(
            db_path=Path(os.getenv("MARKETING_SWARM_DB_PATH", "runtime/marketing_swarm.sqlite3")),
            artifact_dir=Path(os.getenv("MARKETING_SWARM_ARTIFACT_DIR", "runtime/artifacts")),
            llm_provider=os.getenv("MARKETING_SWARM_LLM_PROVIDER", "fake"),
            local_endpoint=os.getenv("MARKETING_SWARM_LOCAL_ENDPOINT", "http://localhost:11434"),
            default_model=os.getenv("MARKETING_SWARM_DEFAULT_MODEL", "local-general"),
            confidence_threshold=float(os.getenv("MARKETING_SWARM_CONFIDENCE_THRESHOLD", "0.68")),
            qa_revision_limit=int(os.getenv("MARKETING_SWARM_QA_REVISION_LIMIT", "2")),
            trace_path=Path(os.getenv("MARKETING_SWARM_TRACE_PATH", "runtime/traces.jsonl")),
            log_level=os.getenv("MARKETING_SWARM_LOG_LEVEL", "INFO"),
        )

    def ensure_dirs(self) -> None:
        """Create runtime directories used by local persistence."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
