from marketing_swarm.tools.registry import build_default_registry


def test_all_default_tools_return_structured_results():
    registry = build_default_registry()
    assert len(registry.names()) >= 16
    for name in registry.names():
        result = registry.run(name, {"query": "Launch campaign with audience message cta proof", "limit": 3})
        assert result.tool == name
        assert result.ok, result.error
        assert "summary" in result.data


def test_tool_failure_is_structured():
    registry = build_default_registry()
    result = registry.run("keyword_seo_scorer", {})
    assert not result.ok
    assert result.error is not None
    assert result.error.component == "keyword_seo_scorer"
