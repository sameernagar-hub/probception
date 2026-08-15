"""The closed loop.

    retrieve -> hypothesise -> design -> score (EIG) -> run -> update -> repeat

Every arrow writes to the ledger before it takes effect. The loop never mutates
belief without first recording what it predicted, so any run can be graded after
the fact on whether its predictions were any good.

This is the module that answers Track A's first criterion directly: the agent
analyses data it has not seen, and the experiment it proposes next is computed
from the posterior — so when the results change, the proposal changes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from probception.adapters.base import ExperimentAdapter, SearchAdapter
from probception.adapters.mock import MockExperimentAdapter, MockSearchAdapter
from probception.agents.scientist import HeuristicScientist, Scientist
from probception.belief.state import BeliefState
from probception.config import settings
from probception.design.eig import Score, choose
from probception.trace.ledger import Ledger
from probception.types import Decision, Evidence, Experiment, Hypothesis, Observation, RunSummary


@dataclass
class StepRecord:
    """Everything that happened in one turn of the loop."""

    step: int
    decision: Decision
    winner: Score
    observation: Observation
    surprise_bits: float
    belief_before: dict[str, float]
    belief_after: dict[str, float]
    entropy_before: float
    entropy_after: float


@dataclass
class ClosedLoop:
    question: str
    scientist: Scientist = field(default_factory=HeuristicScientist)
    searcher: SearchAdapter = field(default_factory=MockSearchAdapter)
    lab: ExperimentAdapter | None = None
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    run_root: str = ""

    def __post_init__(self) -> None:
        self.run_root = self.run_root or str(settings.run_dir)
        self.ledger = Ledger(self.run_id, self.run_root)
        self.evidence: list[Evidence] = []
        self.belief: BeliefState | None = None
        self.history: list[StepRecord] = []
        self.run_counts: dict[str, int] = {}
        self._entropy_start: float = 0.0

    # -- phases ----------------------------------------------------------
    def gather(self, limit: int = 6) -> list[Evidence]:
        """Retrieve evidence and pin it in the ledger before reasoning on it."""
        self.evidence = self.searcher.search(self.question, limit=limit)
        self.ledger.append(
            "evidence_gathered",
            self.evidence,
            note=f"{len(self.evidence)} items from {self.searcher.name}",
        )
        return self.evidence

    def frame(self) -> BeliefState:
        """Turn the question into a scored hypothesis space."""
        hypotheses: list[Hypothesis] = self.scientist.hypothesise(self.question, self.evidence)
        self.belief = BeliefState(hypotheses)
        self._entropy_start = self.belief.entropy
        self.ledger.append(
            "hypotheses_framed",
            {
                "reasoner": self.scientist.name,
                "hypotheses": [h.model_dump(mode="json") for h in hypotheses],
                "prior_entropy_bits": round(self._entropy_start, 4),
            },
            note=f"{len(hypotheses)} competing hypotheses",
        )
        return self.belief

    def propose(self, n: int = 4) -> tuple[Score, list[Score]]:
        """Design candidates and pick the most informative one per unit cost."""
        assert self.belief is not None, "call frame() first"
        candidates: list[Experiment] = self.scientist.design(
            self.question, list(self.belief.hypotheses.values()), self.evidence, n=n
        )
        if not candidates:
            raise RuntimeError("The reasoner produced no scoreable experiments.")
        winner, scored = choose(self.belief, candidates, self.run_counts)
        self.ledger.append(
            "experiments_scored",
            {
                "candidates": [
                    {
                        "id": s.experiment.id,
                        "title": s.experiment.title,
                        "eig_bits": round(s.eig, 4),
                        "cost": s.experiment.cost,
                        "times_run": s.times_run,
                        "novelty": round(s.novelty, 4),
                        "utility": round(s.utility, 4),
                        "predicted_outcomes": {
                            k: round(v, 4) for k, v in s.predicted_outcomes.items()
                        },
                    }
                    for s in scored
                ],
                "chosen": winner.experiment.id,
            },
            note=f"chose '{winner.experiment.title}' at {winner.eig:.3f} bits",
        )
        return winner, scored

    def observe(self, experiment: Experiment) -> Observation:
        """Run the experiment against data the agent has not seen."""
        lab = self.lab or MockExperimentAdapter(seed=settings.seed)
        observation = lab.run(experiment)
        # Record that this protocol has now been used, so a repeat of it is
        # discounted the next time we plan.
        self.run_counts[experiment.id] = self.run_counts.get(experiment.id, 0) + 1
        self.ledger.append(
            "observation",
            observation,
            note=f"{lab.name} returned '{observation.outcome_label}'",
        )
        return observation

    def revise(self, experiment: Experiment, observation: Observation) -> StepRecord:
        """Bayes update. This is the only place belief is allowed to change."""
        assert self.belief is not None
        before = self.belief.as_dict()
        h_before = self.belief.entropy
        surprise = self.belief.surprise(experiment, observation)
        after = self.belief.update(experiment, observation)
        h_after = self.belief.entropy

        record = StepRecord(
            step=len(self.history),
            decision=Decision(
                step=len(self.history),
                chosen_experiment_id=experiment.id,
                expected_information_gain=0.0,
                utility=0.0,
                belief_before=before,
                belief_after=after,
            ),
            winner=None,  # type: ignore[arg-type]
            observation=observation,
            surprise_bits=surprise,
            belief_before=before,
            belief_after=after,
            entropy_before=h_before,
            entropy_after=h_after,
        )
        self.ledger.append(
            "belief_updated",
            {
                "experiment_id": experiment.id,
                "observed": observation.outcome_label,
                "surprise_bits": round(surprise, 4),
                "entropy_before_bits": round(h_before, 4),
                "entropy_after_bits": round(h_after, 4),
                "belief_before": {k: round(v, 5) for k, v in before.items()},
                "belief_after": {k: round(v, 5) for k, v in after.items()},
                "leader": self.belief.leader().statement,
            },
            note=f"entropy {h_before:.3f} -> {h_after:.3f} bits",
        )
        return record

    # -- the whole thing -------------------------------------------------
    def run(self, steps: int = 3, candidates_per_step: int = 4) -> RunSummary:
        """Execute the full loop and return a summary."""
        self.ledger.append(
            "run_started",
            {
                "question": self.question,
                "reasoner": self.scientist.name,
                "searcher": self.searcher.name,
                "lab": (self.lab or MockExperimentAdapter()).name,
                "mode": settings.mode,
                "model": settings.model if self.scientist.name == "claude" else None,
                "steps_requested": steps,
            },
            note="loop start",
        )

        self.gather()
        self.frame()
        assert self.belief is not None

        next_experiment_title: str | None = None
        for i in range(steps):
            winner, _ = self.propose(n=candidates_per_step)
            observation = self.observe(winner.experiment)
            record = self.revise(winner.experiment, observation)
            record.step = i
            record.winner = winner
            record.decision.step = i
            record.decision.expected_information_gain = winner.eig
            record.decision.utility = winner.utility
            record.decision.reasoning = winner.explain()
            record.decision.evidence_ids = [e.id for e in self.evidence]
            self.history.append(record)
            next_experiment_title = winner.experiment.title

        # One more design pass with no execution: this is "what would you do
        # next, given everything you now believe?" — the proposal the
        # counterfactual harness diffs across worlds.
        try:
            final_winner, _ = self.propose(n=candidates_per_step)
            next_experiment_title = final_winner.experiment.title
            self.ledger.append(
                "next_experiment_proposed",
                {
                    "title": final_winner.experiment.title,
                    "protocol": final_winner.experiment.protocol,
                    "eig_bits": round(final_winner.eig, 4),
                    "rationale": final_winner.explain(),
                },
                note="terminal proposal (not executed)",
            )
        except RuntimeError:
            pass

        summary = RunSummary(
            run_id=self.run_id,
            question=self.question,
            steps=len(self.history),
            final_belief=self.belief.labelled(),
            leading_hypothesis=self.belief.leader().statement,
            entropy_start=self._entropy_start,
            entropy_end=self.belief.entropy,
            next_experiment=next_experiment_title,
            ledger_path=str(self.ledger.path),
        )
        self.ledger.append("run_finished", summary, note="loop end")
        return summary
