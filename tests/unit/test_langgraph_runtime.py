from marketing_swarm.orchestration.engine import CampaignEngine
from marketing_swarm.orchestration.graph_builder import CompiledCampaignGraph


def test_campaign_engine_owns_compiled_langgraph(settings):
    engine = CampaignEngine(settings)

    assert isinstance(engine.graph, CompiledCampaignGraph)
    assert engine.graph.compiled.__class__.__module__.startswith("langgraph.")
    assert hasattr(engine.graph.compiled, "ainvoke")
