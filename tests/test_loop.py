"""End-to-end: the loop runs, and — critically — it actually closes."""

from __future__ import annotations

from probception.adapters.mock import MockSearchAdapter, ScriptedExperimentAdapter
from probception.agents.scientist import HeuristicScientist
from probception.eval.calibration import score_run
from probception.eval.counterfactual import World, run_counterfactual, total_variation
from probception.loop import ClosedLoop
from probception.trace.ledger import Ledger
from probception.trace.report import write_report

QUESTION = "Does the treatment change the measured outcome?"


def build(tmp_path, outcomes: list[str], run_id: str = "test") -> ClosedLoop:
    return ClosedLoop(
        question=QUESTION,
        scientist=HeuristicScientist(),
        searcher=MockSearchAdapter(),
        lab=ScriptedExperimentAdapter(outcomes),
        run_id=run_id,
        run_root=str(tmp_path),
    )


def test_loop_runs_and_reduces_uncertainty(tmp_path):
    summary = build(tmp_path, ["positive", "positive", "positive"]).run(steps=3)
    assert summary.steps == 3
    assert summary.entropy_end <= summary.entropy_start
    assert sum(summary.final_belief.values()) == 1.0 or abs(sum(summary.final_belief.values()) - 1) < 1e-9
    assert summary.next_experiment


def test_every_state_change_is_recorded(tmp_path):
    loop = build(tmp_path, ["positive", "negative"])
    loop.run(steps=2)
    events = [e["event"] for e in loop.ledger.read()]
    for required in (
        "run_started",
        "evidence_gathered",
        "hypotheses_framed",
        "experiments_scored",
        "observation",
        "belief_updated",
        "run_finished",
    ):
        assert required in events, f"missing ledger event: {required}"
    ok, message = loop.ledger.verify()
    assert ok, message


def test_opposite_results_produce_opposite_beliefs(tmp_path):
    confirming = build(tmp_path, ["positive"] * 3, run_id="confirm").run(steps=3)
    refuting = build(tmp_path, ["negative"] * 3, run_id="refute").run(steps=3)

    divergence = total_variation(confirming.final_belief, refuting.final_belief)
    assert divergence > 0.1, "results that contradict each other must move belief apart"
    assert confirming.leading_hypothesis != refuting.leading_hypothesis


def test_counterfactual_harness_reports_a_verdict(tmp_path):
    result = run_counterfactual(
        question=QUESTION,
        worlds=[World("up", ["positive"] * 3), World("down", ["negative"] * 3)],
        scientist=HeuristicScientist(),
        steps=3,
        run_root=str(tmp_path),
    )
    assert set(result.proposals) == {"up", "down"}
    assert result.belief_divergence > 0.1
    assert "LOOP" in result.verdict()


def test_calibration_scores_a_finished_run(tmp_path):
    loop = build(tmp_path, ["positive", "positive", "negative"])
    loop.run(steps=3)
    report = score_run(Ledger.load(loop.run_id, str(tmp_path)))
    assert report.n == 3
    assert 0.0 <= report.brier <= 2.0
    assert 0.0 <= report.accuracy <= 1.0


def test_report_is_self_contained(tmp_path):
    loop = build(tmp_path, ["positive", "negative"])
    loop.run(steps=2)
    path = write_report(loop.run_id, str(tmp_path))
    html = path.read_text(encoding="utf-8")
    assert path.exists()
    # No external requests: the demo laptop may be on conference wifi.
    assert "http://" not in html and "https://" not in html
    assert "Decision trail" in html
