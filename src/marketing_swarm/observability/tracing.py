"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from marketing_swarm.schemas.common import new_id, utc_now


@dataclass(slots=True)
class Span:
    """Simple OpenTelemetry-style span envelope."""

    name: str
    span_id: str = field(default_factory=lambda: new_id("span"))
    parent_id: str | None = None
    started_at: float = field(default_factory=time.perf_counter)
    ended_at: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"

    def finish(self, status: str = "ok") -> None:
        """Mark the span complete."""
        self.ended_at = time.perf_counter()
        self.status = status

    def to_record(self) -> dict[str, Any]:
        """Serialize span as a JSON-ready record."""
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "status": self.status,
            "duration_ms": round(((self.ended_at or time.perf_counter()) - self.started_at) * 1000, 3),
            "attributes": self.attributes,
            "timestamp": utc_now().isoformat(),
        }


class TraceRecorder:
    """Append-only JSONL trace recorder."""

    def __init__(self, path: Path | str = "data/traces.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.spans: list[Span] = []

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[Span]:
        """Create and record a span."""
        span = Span(name=name, attributes=attributes)
        try:
            yield span
        except Exception:
            span.finish("error")
            self.record(span)
            raise
        else:
            span.finish("ok")
            self.record(span)

    def record(self, span: Span) -> None:
        """Record a span to memory and disk."""
        self.spans.append(span)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(span.to_record(), sort_keys=True) + "\n")
