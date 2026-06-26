"""Agentic Marketing Swarm module.

MIT License. Copyright (c) 2026 Shake MD Tareq Hasan.
"""
from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from marketing_swarm.schemas.knowledge import KnowledgeSource

DEFAULT_EXTENSIONS = {".md", ".markdown", ".txt", ".json", ".jsonl", ".csv"}


class LocalKnowledgeLoader:
    """Load local files into normalized knowledge sources."""

    def __init__(self, extensions: Iterable[str] | None = None, max_file_bytes: int = 2_000_000) -> None:
        self.extensions = {item.lower() for item in (extensions or DEFAULT_EXTENSIONS)}
        self.max_file_bytes = max_file_bytes

    def load_path(self, path: Path | str, *, namespace: str = "default", recursive: bool = True) -> list[KnowledgeSource]:
        """Load one file or every supported file under a directory."""
        root = Path(path)
        if not root.exists():
            raise FileNotFoundError(f"knowledge path does not exist: {root}")
        if root.is_file():
            return self._load_file(root, namespace=namespace)
        sources: list[KnowledgeSource] = []
        for candidate in self.discover(root, recursive=recursive):
            sources.extend(self._load_file(candidate, namespace=namespace))
        return sources

    def discover(self, root: Path | str, *, recursive: bool = True) -> list[Path]:
        """Discover supported files in stable order."""
        base = Path(root)
        iterator = base.rglob("*") if recursive else base.glob("*")
        paths = [
            path
            for path in iterator
            if path.is_file() and path.suffix.lower() in self.extensions and not path.name.startswith(".")
        ]
        paths.sort(key=lambda item: str(item).lower())
        return paths

    def _load_file(self, path: Path, *, namespace: str) -> list[KnowledgeSource]:
        """Load one supported file."""
        if path.suffix.lower() not in self.extensions:
            return []
        size = path.stat().st_size
        if size > self.max_file_bytes:
            raise ValueError(f"knowledge file is too large: {path} ({size} bytes)")
        suffix = path.suffix.lower()
        if suffix in {".md", ".markdown", ".txt"}:
            text = self._read_text(path)
            return [KnowledgeSource.from_path(path, text, namespace=namespace)]
        if suffix == ".json":
            return self._load_json(path, namespace=namespace)
        if suffix == ".jsonl":
            return self._load_jsonl(path, namespace=namespace)
        if suffix == ".csv":
            return self._load_csv(path, namespace=namespace)
        return []

    def _read_text(self, path: Path) -> str:
        """Read text with a forgiving local fallback."""
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        cleaned = text.strip()
        if not cleaned:
            raise ValueError(f"knowledge file is empty: {path}")
        return cleaned

    def _load_json(self, path: Path, *, namespace: str) -> list[KnowledgeSource]:
        """Load a JSON file as one or more sources."""
        data = json.loads(self._read_text(path))
        if isinstance(data, list):
            sources = []
            for index, item in enumerate(data):
                text = self._flatten_json(item)
                title = self._title_from_json(item, fallback=f"{path.stem} {index + 1}")
                sources.append(
                    KnowledgeSource.from_path(
                        path,
                        text,
                        namespace=namespace,
                        title=title,
                        metadata={"json_index": index, "record_type": type(item).__name__},
                    )
                )
            return sources
        text = self._flatten_json(data)
        title = self._title_from_json(data, fallback=path.stem)
        return [KnowledgeSource.from_path(path, text, namespace=namespace, title=title)]

    def _load_jsonl(self, path: Path, *, namespace: str) -> list[KnowledgeSource]:
        """Load newline-delimited JSON records."""
        sources: list[KnowledgeSource] = []
        for index, line in enumerate(self._read_text(path).splitlines()):
            if not line.strip():
                continue
            data = json.loads(line)
            title = self._title_from_json(data, fallback=f"{path.stem} {index + 1}")
            sources.append(
                KnowledgeSource.from_path(
                    path,
                    self._flatten_json(data),
                    namespace=namespace,
                    title=title,
                    metadata={"jsonl_line": index + 1, "record_type": type(data).__name__},
                )
            )
        return sources

    def _load_csv(self, path: Path, *, namespace: str) -> list[KnowledgeSource]:
        """Load a CSV file as row-level sources plus a compact table summary."""
        text = self._read_text(path)
        rows = list(csv.DictReader(text.splitlines()))
        if not rows:
            return [KnowledgeSource.from_path(path, text, namespace=namespace)]
        sources: list[KnowledgeSource] = []
        headings = list(rows[0].keys())
        summary_lines = [f"Columns: {', '.join(headings)}", f"Rows: {len(rows)}"]
        summary_lines.extend(self._row_to_text(row, headings) for row in rows[:20])
        sources.append(
            KnowledgeSource.from_path(
                path,
                "\n".join(summary_lines),
                namespace=namespace,
                title=f"{path.stem} table summary",
                metadata={"csv_rows": len(rows), "csv_columns": headings, "summary": True},
            )
        )
        for index, row in enumerate(rows):
            title = str(row.get("title") or row.get("name") or row.get("campaign") or f"{path.stem} row {index + 1}")
            sources.append(
                KnowledgeSource.from_path(
                    path,
                    self._row_to_text(row, headings),
                    namespace=namespace,
                    title=title,
                    metadata={"csv_row": index + 1, "csv_columns": headings},
                )
            )
        return sources

    def _row_to_text(self, row: dict[str, Any], headings: list[str]) -> str:
        """Render a CSV row as searchable text."""
        return "\n".join(f"{heading}: {row.get(heading, '')}" for heading in headings if str(row.get(heading, "")).strip())

    def _title_from_json(self, data: Any, *, fallback: str) -> str:
        """Infer a useful source title from JSON-like content."""
        if isinstance(data, dict):
            for key in ("title", "name", "campaign", "id"):
                value = data.get(key)
                if value:
                    return str(value)[:120]
        return fallback.replace("-", " ").replace("_", " ").title()

    def _flatten_json(self, value: Any, *, prefix: str = "") -> str:
        """Flatten JSON into readable text for retrieval."""
        lines: list[str] = []
        if isinstance(value, dict):
            for key, item in value.items():
                child_prefix = f"{prefix}.{key}" if prefix else str(key)
                lines.append(self._flatten_json(item, prefix=child_prefix))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                child_prefix = f"{prefix}[{index}]"
                lines.append(self._flatten_json(item, prefix=child_prefix))
        else:
            label = prefix or "value"
            lines.append(f"{label}: {value}")
        return "\n".join(line for line in lines if line.strip())

