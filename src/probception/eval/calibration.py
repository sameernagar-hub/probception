"""Calibration: is the agent's confidence worth anything?

An agent that says "80% likely" should be right about 80% of the time. We record
every prediction before the result arrives, so this is measurable rather than
rhetorical. Brier score is the headline number; the reliability table is what
you actually show a scientist.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from probception.trace.ledger import Ledger


@dataclass
class CalibrationReport:
    n: int
    brier: float
    """Mean squared error of predicted probability vs outcome. Lower is better;
    0.25 is what you get by always guessing 50/50 on a binary question."""
    log_score: float
    """Mean surprise in bits. Lower is better."""
    accuracy: float
    """How often the highest-probability outcome was the one observed."""
    bins: list[dict] = field(default_factory=list)
    baseline_brier: float = 0.25

    @property
    def beats_baseline(self) -> bool:
        return self.brier < self.baseline_brier

    def summary(self) -> str:
        verdict = "better than" if self.beats_baseline else "no better than"
        return (
            f"n={self.n} predictions | Brier {self.brier:.4f} ({verdict} the "
            f"{self.baseline_brier:.2f} uninformed baseline) | "
            f"log score {self.log_score:.3f} bits | top-1 accuracy {self.accuracy:.1%}"
        )


def score_run(ledger: Ledger) -> CalibrationReport:
    """Grade a completed run from its ledger alone — no live model needed."""
    scored = ledger.events("experiments_scored")
    updates = ledger.events("belief_updated")

    predictions: list[tuple[dict[str, float], str]] = []
    by_experiment: dict[str, dict[str, float]] = {}
    for event in scored:
        chosen = event["payload"]["chosen"]
        for cand in event["payload"]["candidates"]:
            if cand["id"] == chosen:
                by_experiment[chosen] = cand["predicted_outcomes"]

    for event in updates:
        exp_id = event["payload"]["experiment_id"]
        observed = event["payload"]["observed"]
        if exp_id in by_experiment:
            predictions.append((by_experiment[exp_id], observed))

    if not predictions:
        return CalibrationReport(n=0, brier=float("nan"), log_score=float("nan"), accuracy=0.0)

    import math

    brier_total = 0.0
    log_total = 0.0
    correct = 0
    bin_acc: dict[int, list[int]] = {}

    for predicted, observed in predictions:
        for label, p in predicted.items():
            actual = 1.0 if label == observed else 0.0
            brier_total += (p - actual) ** 2
        p_obs = max(predicted.get(observed, 1e-9), 1e-9)
        log_total += -math.log2(p_obs)
        top = max(predicted.items(), key=lambda kv: kv[1])[0]
        correct += int(top == observed)

        bucket = min(int(p_obs * 10), 9)
        bin_acc.setdefault(bucket, []).append(1)

    n = len(predictions)
    n_outcomes = sum(len(p) for p, _ in predictions) or 1
    bins = [
        {"bin": f"{b/10:.1f}-{(b+1)/10:.1f}", "count": len(v)}
        for b, v in sorted(bin_acc.items())
    ]

    return CalibrationReport(
        n=n,
        brier=brier_total / n_outcomes,
        log_score=log_total / n,
        accuracy=correct / n,
        bins=bins,
    )
