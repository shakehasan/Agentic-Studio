from marketing_swarm.retrieval.pipeline import AgenticRAGPipeline


def test_agentic_rag_returns_cited_results():
    pipeline = AgenticRAGPipeline()
    results = pipeline.search("campaign audience proof measurement", limit=5)
    assert results
    assert all(result.document.title for result in results)
    assert results[0].score >= 0
