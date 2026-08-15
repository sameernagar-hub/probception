"""The counterfactual harness — our answer to "does the loop actually close?"

Claiming an agent adapts to results is cheap. This module makes it falsifiable:
run the *identical* agent, same question, same seed, same reasoner, against two
worlds whose experimental results differ, then diff what it proposes next.

If the proposal is identical across worlds, the loop is open and we say so.
A negative result here is a real finding about our own system, and we report it
rather than hiding it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from probception.adapters.mock import MockSearchAdapter, ScriptedExperimentAdapter
from probception.agents.scientist import HeuristicScientist, Scientist
from probception.loop import ClosedLoop
from probception.types import RunSummary


@dataclass
class World:
    """A named sequence of experimental outcomes to replay."""

    name: str
    outcomes: list[str]


@dataclass
class CounterfactualResult:
    worlds: list[World]
    summaries: dict[str, RunSummary]
    proposals: dict[str, str | None]
    leaders: dict[str, str]
    beliefs: dict[str, dict[str, float]]
    responsive: bool = False
    belief_divergence: float = 0.0
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "responsive": self.responsive,
            "belief_divergence": round(self.belief_divergence, 4),
            "proposals": self.proposals,
            "leaders": self.leaders,
            "beliefs": self.beliefs,
            "notes": self.notes,
        }

    def verdict(self) -> str:
        if self.responsive:
            return (
                "CLOSED LOOP: different results produced a different next experiment. "
                f"Belief divergence {self.belief_divergence:.3f} (total variation)."
            )
        if self.belief_divergence > 0.05:
            return (
                "PARTIALLY CLOSED: beliefs moved apart "
                f"({self.belief_divergence:.3f}) but the top-ranked next experiment "
                "was the same in both worlds."
            )
        return "OPEN LOOP: results did not change the agent's beliefs or its proposal."


def total_variation(a: dict[str, float], b: dict[str, float]) -> float:
    """Total-variation distance between two belief distributions, keyed by statement."""
    keys = set(a) | set(b)
    return 0.5 * sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys)


def run_counterfactual(
    question: str,
    worlds: list[World] | None = None,
    scientist: Scientist | None = None,
    steps: int = 3,
    run_root: str = "runs",
) -> CounterfactualResult:
    """Replay one agent across several scripted worlds and diff the outcome."""
    worlds = worlds or [
        World("confirming", ["positive", "positive", "positive"]),
        World("refuting", ["negative", "negative", "negative"]),
    ]
    scientist = scientist or HeuristicScientist()

    summaries: dict[str, RunSummary] = {}
    proposals: dict[str, str | None] = {}
    leaders: dict[str, str] = {}
    beliefs: dict[str, dict[str, float]] = {}

    for world in worlds:
        loop = ClosedLoop(
            question=question,
            scientist=scientist,
            searcher=MockSearchAdapter(),
            lab=ScriptedExperimentAdapter(world.outcomes),
            run_id=f"cf-{world.name}",
            run_root=run_root,
        )
        summary = loop.run(steps=steps)
        summaries[world.name] = summary
        proposals[world.name] = summary.next_experiment
        leaders[world.name] = summary.leading_hypothesis
        beliefs[world.name] = summary.final_belief

    names = [w.name for w in worlds]
    distinct_proposals = {proposals[n] for n in names}
    divergence = max(
        (
            total_variation(beliefs[a], beliefs[b])
            for i, a in enumerate(names)
            for b in names[i + 1 :]
        ),
        default=0.0,
    )

    result = CounterfactualResult(
        worlds=worlds,
        summaries=summaries,
        proposals=proposals,
        leaders=leaders,
        beliefs=beliefs,
        responsive=len(distinct_proposals) > 1,
        belief_divergence=divergence,
    )
    if len(distinct_proposals) == 1:
        result.notes.append(
            "The top proposal matched across worlds. Check whether the candidate set is "
            "too narrow to express a different next step, or whether the outcomes genuinely "
            "point the same way."
        )
    if divergence < 1e-6:
        result.notes.append(
            "Beliefs did not move at all. That usually means the likelihood tables do not "
            "discriminate between hypotheses — the experiments are uninformative by construction."
        )
    return result
