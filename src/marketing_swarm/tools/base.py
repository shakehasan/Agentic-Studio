"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import re
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from marketing_swarm.schemas.common import FailureKind, FailureStamp
from marketing_swarm.schemas.tools import ToolResult


@dataclass(slots=True)
class ToolContext:
    """Context passed to every tool."""

    run_id: str | None = None
    agent: str | None = None
    knowledge_base: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseTool:
    """Typed, validated, deterministic base class for local tools."""

    name = "base"
    description = "Base tool"
    timeout_seconds = 10.0

    def schema(self) -> dict[str, Any]:
        """Return the input schema."""
        return {"type": "object"}

    def run(self, payload: Mapping[str, Any], context: ToolContext | None = None) -> ToolResult:
        """Run the tool and return a structured result or failure stamp."""
        started = time.perf_counter()
        context = context or ToolContext()
        try:
            self._validate(payload)
            data = self._run(payload, context)
            return ToolResult(tool=self.name, ok=True, data=data, elapsed_ms=(time.perf_counter() - started) * 1000)
        except Exception as exc:
            stamp = FailureStamp(
                kind=FailureKind.TOOL,
                message=str(exc),
                retryable=False,
                component=self.name,
                details={"payload_keys": sorted(payload.keys())},
            )
            return ToolResult(tool=self.name, ok=False, error=stamp, elapsed_ms=(time.perf_counter() - started) * 1000)

    def _validate(self, payload: Mapping[str, Any]) -> None:
        """Validate common input constraints."""
        schema = self.schema()
        for required_field in schema.get("required", []):
            if required_field not in payload:
                raise ValueError(f"missing required field: {required_field}")

    def _run(self, payload: Mapping[str, Any], context: ToolContext) -> dict[str, Any]:
        """Execute the tool."""
        raise NotImplementedError

    def _require_text(self, payload: Mapping[str, Any], key: str) -> str:
        """Return a non-empty text field."""
        value = str(payload.get(key, "")).strip()
        if not value:
            raise ValueError(f"{key} must be non-empty text")
        return value

    def _keywords(self, text: str) -> list[str]:
        """Extract deterministic keywords."""
        stop = {"the", "and", "for", "with", "that", "this", "from", "into", "your", "their", "about"}
        words = [
            word.strip(".,:;!?()[]{}").lower()
            for word in text.split()
            if len(word.strip(".,:;!?()[]{}")) > 3
        ]
        return list(dict.fromkeys(word for word in words if word not in stop))[:30]

    def _rank_documents(
        self,
        query: str,
        tokens: list[str],
        documents: list[Any],
        limit: int,
    ) -> list[dict[str, Any]]:
        """Rank local documents by lexical overlap."""
        if not documents:
            documents = [
                {"title": "Local campaign playbook", "text": query, "source": "generated:brief"},
                {"title": "Measurement playbook", "text": "activation retention conversion measurement proof", "source": "generated:metrics"},
            ]
        scored: list[tuple[float, dict[str, Any]]] = []
        token_set = set(tokens)
        for index, document in enumerate(documents):
            if isinstance(document, Mapping):
                title = str(document.get("title", f"Document {index + 1}"))
                text = str(document.get("text") or document.get("body") or document)
                source = str(document.get("source", "local"))
            else:
                title = getattr(document, "title", f"Document {index + 1}")
                text = getattr(document, "text", str(document))
                source = getattr(document, "source", "local")
            haystack = text.lower()
            overlap = sum(1 for token in token_set if token in haystack)
            density = overlap / max(1, len(token_set))
            score = min(1.0, 0.25 + density + min(0.2, len(text) / 2000))
            scored.append((score, {"title": title, "excerpt": text[:260], "source": source, "score": round(score, 3)}))
        scored.sort(key=lambda row: row[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def _keyword_clusters(self, tokens: list[str]) -> list[dict[str, Any]]:
        """Build keyword clusters."""
        clusters = []
        for index, token in enumerate(tokens[:8], start=1):
            clusters.append(
                {
                    "cluster": token,
                    "intent": ["informational", "commercial", "comparative", "activation"][index % 4],
                    "terms": [token, f"{token} guide", f"{token} examples", f"best {token}"],
                    "priority": max(1, 10 - index),
                    "geo_note": "Write citation-friendly answer blocks and concise definitions.",
                }
            )
        return clusters

    def _readability(self, text: str) -> dict[str, Any]:
        """Compute readability heuristics."""
        sentences = [part for part in re.split(r"[.!?]+", text) if part.strip()]
        words = [word for word in re.findall(r"[A-Za-z0-9']+", text) if word]
        avg = len(words) / max(1, len(sentences))
        score = max(0, min(100, int(100 - avg * 2.2)))
        return {
            "score": score,
            "grade": "clear" if score >= 60 else "dense",
            "sentence_count": len(sentences),
            "word_count": len(words),
            "recommendations": [
                "Use shorter lead sentences.",
                "Replace abstract claims with concrete proof.",
                "Keep calls to action visually distinct.",
            ],
        }

    def _tone(self, tokens: list[str], text: str) -> dict[str, Any]:
        """Classify tone and sentiment."""
        lower = text.lower()
        urgent = any(word in lower for word in ["now", "urgent", "immediately", "deadline"])
        trust = any(word in lower for word in ["secure", "privacy", "safe", "control", "proof"])
        return {
            "tone": "assured" if trust else "practical" if not urgent else "urgent",
            "sentiment": "positive" if any(word in lower for word in ["growth", "win", "improve"]) else "neutral",
            "urgency": "high" if urgent else "moderate",
            "style_terms": tokens[:6],
        }

    def _personas(self, tokens: list[str], limit: int) -> list[dict[str, Any]]:
        """Create persona candidates."""
        personas = []
        for index in range(min(4, limit)):
            seed = tokens[index % max(1, len(tokens))] if tokens else "buyer"
            personas.append(
                {
                    "name": f"{seed.title()} Operator",
                    "job_to_be_done": f"Make progress on {seed} without adding operational drag.",
                    "pain_points": ["unclear tradeoffs", "slow evaluation", "risk of choosing poorly"],
                    "buying_triggers": ["new initiative", "team growth", "tool consolidation"],
                    "message": f"Show how the offer improves {seed} with practical proof.",
                }
            )
        return personas

    def _calendar(self, tokens: list[str], payload: Mapping[str, Any], limit: int) -> list[dict[str, Any]]:
        """Build calendar items."""
        channel = str(payload.get("channel", "owned content"))
        terms = tokens or ["launch", "proof", "conversion"]
        return [
            {
                "week": week,
                "channel": channel if week % 2 else "email",
                "theme": terms[(week - 1) % len(terms)],
                "asset": ["pillar article", "social thread", "newsletter", "landing page"][week % 4],
                "goal": ["awareness", "engagement", "activation", "learning"][week % 4],
            }
            for week in range(1, min(limit, 12) + 1)
        ]

    def _template(self, query: str, tokens: list[str], payload: Mapping[str, Any]) -> dict[str, Any]:
        """Render a structured template."""
        sections = [
            {"heading": "Insight", "body": f"The strongest signal is {tokens[0] if tokens else 'audience clarity'}."},
            {"heading": "Message", "body": query[:220]},
            {"heading": "Action", "body": "Ship a measurable asset, observe response, and iterate."},
        ]
        return {"title": str(payload.get("title", "Campaign Artifact")), "sections": sections}

    def _asset_spec(self, query: str, tokens: list[str], payload: Mapping[str, Any]) -> dict[str, Any]:
        """Return safe markdown artifact metadata."""
        stem = "-".join((tokens or ["campaign", "asset"])[:6])
        filename = re.sub(r"[^a-z0-9-]+", "-", stem.lower()).strip("-") + ".md"
        return {"filename": filename, "body": query, "safe": True}

    def _claims(self, text: str) -> list[dict[str, Any]]:
        """Extract claim-like sentences."""
        claims = []
        for index, sentence in enumerate([part.strip() for part in re.split(r"[.!?]+", text) if part.strip()], start=1):
            if any(marker in sentence.lower() for marker in ["will", "can", "increase", "reduce", "best", "most", "%"]):
                claims.append({"id": f"claim_{index}", "claim": sentence, "needs_citation": True, "risk": "medium"})
        return claims

    def _redact(self, text: str) -> dict[str, Any]:
        """Redact sensitive strings."""
        patterns = [
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            r"\b\+?\d[\d\s().-]{7,}\d\b",
            r"\b\d{3}-\d{2}-\d{4}\b",
        ]
        redacted = text
        count = 0
        for pattern in patterns:
            redacted, replacements = re.subn(pattern, "[REDACTED]", redacted)
            count += replacements
        return {"text": redacted, "redaction_count": count}

    def _validate_artifact(self, text: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Validate artifact completeness and risk."""
        required = ["audience", "message", "cta"]
        lower = text.lower()
        missing = [item for item in required if item not in lower]
        verdict = "pass" if not missing and len(text.split()) >= 40 else "revise"
        return {
            "verdict": verdict,
            "summary": "Artifact passes completeness checks." if verdict == "pass" else "Artifact needs targeted revision.",
            "missing": missing,
            "confidence": 0.86 if verdict == "pass" else 0.61,
            "checks": {"word_count": len(text.split()), "has_citation_marker": "[" in text and "]" in text},
        }

    def _route(self, query: str, tokens: list[str]) -> dict[str, Any]:
        """Classify routing mode."""
        lower = query.lower()
        if any(word in lower for word in ["launch", "go-to-market", "campaign"]):
            mode = "parallel_launch"
            agents = ["market_research", "competitive_intelligence", "content_strategy", "copywriter", "seo_geo"]
            confidence = 0.88
        elif "email" in lower:
            mode = "deterministic_email"
            agents = ["market_research", "email_marketing", "brand_voice_qa", "analytics_optimization"]
            confidence = 0.82
        elif "seo" in lower or "search" in lower:
            mode = "deterministic_search"
            agents = ["market_research", "seo_geo", "content_strategy", "brand_voice_qa"]
            confidence = 0.82
        else:
            mode = "semantic"
            agents = ["market_research", "content_strategy", "copywriter", "brand_voice_qa", "analytics_optimization"]
            confidence = 0.7 if tokens else 0.52
        return {"mode": mode, "agents": agents, "confidence": confidence, "reason": "local intent heuristics"}

    def _experiments(self, tokens: list[str], limit: int) -> list[dict[str, Any]]:
        """Create experiment designs."""
        terms = tokens or ["message", "offer", "channel"]
        experiments = []
        for index in range(min(limit, 8)):
            term = terms[index % len(terms)]
            experiments.append(
                {
                    "hypothesis": f"If the {term} promise is made more concrete, qualified engagement will improve.",
                    "variant_a": f"Current {term} message",
                    "variant_b": f"Proof-led {term} message",
                    "primary_metric": ["click-through rate", "activation rate", "reply rate", "qualified conversion"][index % 4],
                    "minimum_runtime_days": 14,
                    "decision_rule": "Ship winner only after practical significance and no quality regression.",
                }
            )
        return experiments
