from marketing_swarm.memory.manager import MemoryManager


def test_memory_manager_seeds_procedural_memory():
    manager = MemoryManager()
    summary = manager.summarize()
    assert summary["procedural"]["records"] > 100
    context = manager.retrieve_context("content activation proof", limit=3)
    assert context["procedural"]
