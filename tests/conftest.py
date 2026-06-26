from pathlib import Path
from uuid import uuid4

import pytest

from marketing_swarm.config.settings import Settings


@pytest.fixture()
def settings():
    base = Path("test_artifacts") / uuid4().hex
    base.mkdir(parents=True, exist_ok=True)
    return Settings(db_path=base / "test.sqlite3", artifact_dir=base / "artifacts", trace_path=base / "traces.jsonl")
