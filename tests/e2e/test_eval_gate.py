from marketing_swarm.evals.harness import EvalHarness


def test_eval_gate_passes():
    report = EvalHarness().run()
    assert report.passed
    assert report.routing_score >= 0.8
    assert report.quality_score >= 0.65
