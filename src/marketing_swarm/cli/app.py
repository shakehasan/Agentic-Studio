"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from marketing_swarm.evals.harness import EvalHarness
from marketing_swarm.knowledge.index import KnowledgeBaseService
from marketing_swarm.orchestration.engine import CampaignEngine
from marketing_swarm.persistence.repository import SQLiteRepository
from marketing_swarm.schemas.brief import CampaignBrief

app = typer.Typer(help="Agentic Marketing Swarm CLI")
eval_app = typer.Typer(help="Run eval harness and gates")
kb_app = typer.Typer(help="Manage local knowledge base")
app.add_typer(eval_app, name="eval")
app.add_typer(kb_app, name="kb")
console = Console()


@app.command()
def run(brief: str, output: Path | None = None) -> None:
    """Run a campaign brief locally."""
    state = asyncio.run(CampaignEngine().run(CampaignBrief.from_text(brief)))
    console.print(f"Run: {state.run_id} status={state.status.value}")
    if state.package:
        markdown = state.package.to_markdown()
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown, encoding="utf-8")
            console.print(f"Wrote {output}")
        else:
            console.print(markdown)


@app.command()
def inspect(limit: int = 10) -> None:
    """Inspect recent runs."""
    table = Table("Run", "Status", "Brief")
    for row in SQLiteRepository().list_runs(limit):
        table.add_row(row["id"], row["status"], row["brief"][:80])
    console.print(table)


@eval_app.command("run")
def eval_run(gate: bool = False) -> None:
    """Run deterministic evals."""
    report = EvalHarness().run()
    console.print(report.to_markdown())
    if gate and not report.passed:
        raise typer.Exit(code=1)


@kb_app.command("seed")
def kb_seed() -> None:
    """Seed the default local knowledge base."""
    engine = CampaignEngine()
    console.print(f"Seeded memory tiers: {engine.memory.summarize()}")


@kb_app.command("import")
def kb_import(
    path: Path,
    namespace: str = "default",
    recursive: bool = True,
    target_tokens: int = 220,
    overlap_tokens: int = 36,
) -> None:
    """Import local markdown, text, JSON, JSONL, or CSV files into the knowledge base."""
    service = KnowledgeBaseService.with_chunking(target_tokens=target_tokens, overlap_tokens=overlap_tokens)
    report = service.ingest_path(path, namespace=namespace, recursive=recursive)
    console.print(report.to_markdown())
    if report.errors:
        raise typer.Exit(code=1)


@kb_app.command("search")
def kb_search(query: str, namespace: str | None = None, limit: int = 8) -> None:
    """Search the local knowledge base."""
    service = KnowledgeBaseService()
    hits = service.search(query, namespace=namespace, limit=limit)
    table = Table("Score", "Title", "Excerpt")
    for hit in hits:
        table.add_row(f"{hit.score:.3f}", hit.title, hit.excerpt.replace("\n", " ")[:120])
    console.print(table)


@kb_app.command("manifest")
def kb_manifest(namespace: str | None = None) -> None:
    """Show a compact knowledge-base manifest."""
    service = KnowledgeBaseService()
    console.print(service.manifest(namespace=namespace))


if __name__ == "__main__":
    app()
