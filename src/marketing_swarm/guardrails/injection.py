"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

SUSPICIOUS_PHRASES = [
    "ignore previous instructions",
    "system prompt",
    "developer message",
    "exfiltrate",
    "disable safety",
    "hidden instructions",
]


def injection_risk(text: str) -> dict[str, object]:
    """Return prompt-injection risk signals."""
    lower = text.lower()
    hits = [phrase for phrase in SUSPICIOUS_PHRASES if phrase in lower]
    return {"risk": "high" if hits else "low", "hits": hits, "blocked": bool(hits)}
