"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import re

PII_PATTERNS = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b\+?\d[\d\s().-]{7,}\d\b"),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
]


def redact_pii(text: str) -> tuple[str, int]:
    """Redact deterministic sensitive patterns."""
    redacted = text
    count = 0
    for pattern in PII_PATTERNS:
        redacted, replacements = pattern.subn("[REDACTED]", redacted)
        count += replacements
    return redacted, count
