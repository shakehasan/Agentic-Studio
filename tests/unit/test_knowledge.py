from pathlib import Path
from uuid import uuid4

from marketing_swarm.knowledge.chunking import ChunkingConfig, TextChunker
from marketing_swarm.knowledge.index import KnowledgeBaseService
from marketing_swarm.knowledge.loaders import LocalKnowledgeLoader
from marketing_swarm.persistence.repository import SQLiteRepository
from marketing_swarm.schemas.knowledge import KnowledgeSource


def test_chunker_creates_stable_chunks():
    source = KnowledgeSource(
        namespace="test",
        title="Messaging Notes",
        uri="memory://messaging",
        text=" ".join(f"Audience proof message action sentence {index}." for index in range(80)),
    )
    chunker = TextChunker(ChunkingConfig(target_tokens=80, overlap_tokens=12, min_tokens=10))
    chunks = chunker.chunk_source(source)
    assert len(chunks) > 1
    assert chunks[0].id.startswith("kchunk_")
    assert chunks[0].namespace == "test"
    assert chunks[0].to_document().metadata["source_id"] == source.id


def local_test_dir(name: str) -> Path:
    """Create a workspace-local test directory without pytest temp fixtures."""
    path = Path("test_artifacts") / name / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_loader_reads_markdown_json_and_csv():
    root = local_test_dir("knowledge_loader")
    notes = root / "notes.md"
    notes.write_text("# Launch Notes\n\nAudience message proof action.", encoding="utf-8")
    data = root / "records.json"
    data.write_text('[{"title":"Persona A","pain":"slow evaluation","message":"clear proof"}]', encoding="utf-8")
    table = root / "calendar.csv"
    table.write_text("title,channel,message\nWeek 1,email,Proof-led launch\n", encoding="utf-8")

    loader = LocalKnowledgeLoader()
    sources = loader.load_path(root, namespace="campaign")

    assert len(sources) == 4
    assert {source.namespace for source in sources} == {"campaign"}
    assert any(source.title == "Persona A" for source in sources)
    assert any("Proof-led launch" in source.text for source in sources)


def test_knowledge_service_ingests_persists_and_searches():
    base = local_test_dir("knowledge_service")
    root = base / "kb"
    root.mkdir()
    (root / "strategy.md").write_text(
        "# Strategy\n\nAudience operators need proof-rich messaging, clear action, and measurable activation loops. "
        * 10,
        encoding="utf-8",
    )
    repository = SQLiteRepository(base / "kb.sqlite3")
    service = KnowledgeBaseService.with_chunking(repository=repository, target_tokens=90, overlap_tokens=10)

    report = service.ingest_path(root, namespace="launch")
    hits = service.search("proof messaging activation", namespace="launch", limit=3)
    manifest = service.manifest(namespace="launch")

    assert report.ok
    assert report.chunk_count >= 1
    assert hits
    assert hits[0].score >= 0
    assert manifest["source_count"] == 1
