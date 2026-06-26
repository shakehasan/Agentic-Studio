"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from marketing_swarm.schemas.artifacts import Asset


def validate_asset(asset: Asset) -> dict[str, object]:
    """Validate a campaign asset for minimum completeness."""
    words = asset.body.split()
    missing = []
    lower = asset.body.lower()
    for required in ["audience", "message", "action"]:
        if required not in lower:
            missing.append(required)
    return {
        "asset": asset.name,
        "word_count": len(words),
        "missing": missing,
        "verdict": "pass" if len(words) >= 40 and not missing else "revise",
    }
