"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from statistics import mean
from typing import Any


@dataclass(slots=True)
class MetricPoint:
    """Metric point with labels."""

    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)


class MetricsRegistry:
    """In-memory metrics registry that can be exported as JSON."""

    def __init__(self) -> None:
        self.counters: dict[str, float] = defaultdict(float)
        self.observations: dict[str, list[MetricPoint]] = defaultdict(list)

    def _key(self, name: str, labels: dict[str, str] | None = None) -> str:
        label_text = ",".join(f"{k}={v}" for k, v in sorted((labels or {}).items()))
        return f"{name}{{{label_text}}}"

    def increment(self, name: str, labels: dict[str, str] | None = None, amount: float = 1.0) -> None:
        """Increment a counter."""
        self.counters[self._key(name, labels)] += amount

    def observe(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Record an observation."""
        self.observations[name].append(MetricPoint(name=name, value=value, labels=labels or {}))

    def snapshot(self) -> dict[str, Any]:
        """Return a compact metrics snapshot."""
        observations: dict[str, dict[str, float]] = {}
        for name, points in self.observations.items():
            values = [point.value for point in points]
            observations[name] = {
                "count": float(len(values)),
                "min": min(values) if values else 0.0,
                "max": max(values) if values else 0.0,
                "mean": mean(values) if values else 0.0,
            }
        return {"counters": dict(self.counters), "observations": observations}
