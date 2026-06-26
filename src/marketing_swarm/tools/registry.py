"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

from typing import Any

from .artifact_validator import ArtifactValidatorTool
from .base import BaseTool, ToolContext
from .calendar_builder import CalendarBuilderTool
from .claim_extractor import ClaimExtractorTool
from .experiment_designer import ExperimentDesignerTool
from .hybrid_search import HybridSearchTool
from .keyword_seo_scorer import KeywordSeoScorerTool
from .markdown_asset_writer import MarkdownAssetWriterTool
from .persona_synthesizer import PersonaSynthesizerTool
from .pii_redactor import PiiRedactorTool
from .readability_analyzer import ReadabilityAnalyzerTool
from .reranker import RerankerTool
from .research_corpus import ResearchCorpusTool
from .route_classifier import RouteClassifierTool
from .template_renderer import TemplateRendererTool
from .tone_sentiment_analyzer import ToneSentimentAnalyzerTool
from .vector_search import VectorSearchTool


class ToolRegistry:
    """Registry and execution facade for typed tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        """Return a registered tool or raise a deterministic error."""
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"tool not registered: {name}") from exc

    def run(self, name: str, payload: dict[str, Any], context: ToolContext | None = None):
        """Run a registered tool."""
        return self.get(name).run(payload, context)

    def schemas(self) -> dict[str, dict[str, Any]]:
        """Return tool schemas for model/tool-call planning."""
        return {name: tool.schema() for name, tool in self._tools.items()}

    def names(self) -> list[str]:
        """Return registered tool names."""
        return sorted(self._tools)


def build_default_registry() -> ToolRegistry:
    """Build the default local tool catalog."""
    registry = ToolRegistry()
    registry.register(ResearchCorpusTool())
    registry.register(VectorSearchTool())
    registry.register(HybridSearchTool())
    registry.register(RerankerTool())
    registry.register(KeywordSeoScorerTool())
    registry.register(ReadabilityAnalyzerTool())
    registry.register(ToneSentimentAnalyzerTool())
    registry.register(PersonaSynthesizerTool())
    registry.register(CalendarBuilderTool())
    registry.register(TemplateRendererTool())
    registry.register(MarkdownAssetWriterTool())
    registry.register(ClaimExtractorTool())
    registry.register(PiiRedactorTool())
    registry.register(ArtifactValidatorTool())
    registry.register(RouteClassifierTool())
    registry.register(ExperimentDesignerTool())
    return registry
