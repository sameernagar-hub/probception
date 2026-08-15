"""Offline adapters. Zero credentials, fully deterministic, always available.

These exist so that (a) a new teammate can clone the repo and see the whole loop
run in under a minute, (b) CI can test the reasoning layer without secrets, and
(c) the counterfactual harness can replay the same agent against different
worlds. They are not a toy: the ground-truth world model here is exactly the
interface a real assay plugs into.
"""

from __future__ import annotations

import random

from probception.adapters.base import ExperimentAdapter, SearchAdapter
from probception.types import Evidence, Experiment, Observation, SourceKind

_CORPUS: list[tuple[SourceKind, str, str, float]] = [
    (
        SourceKind.PAPER,
        "10.1038/s41586-021-03819-2",
        "Structure prediction accuracy degrades sharply for sequences with fewer than 30 homologs.",
        0.8,
    ),
    (
        SourceKind.PAPER,
        "10.1126/science.ade2574",
        "Language-model embeddings capture fitness effects without any structural input.",
        0.7,
    ),
    (
        SourceKind.DATASET,
        "ProteinGym:DMS_substitutions",
        "Deep mutational scanning covers 217 assays across 187 proteins.",
        0.9,
    ),
    (
        SourceKind.DATABASE,
        "UniProt:P00533",
        "EGFR kinase domain tolerates substitution at the gatekeeper residue with reduced affinity.",
        0.6,
    ),
    (
        SourceKind.CLINICAL_TRIAL,
        "NCT04185883",
        "Response rate was not stratified by variant class in the reported cohort.",
        0.5,
    ),
    (
        SourceKind.PAPER,
        "10.1101/2023.07.05.547496",
        "Thermostability and catalytic activity trade off in directed evolution campaigns.",
        0.7,
    ),
]


class MockSearchAdapter(SearchAdapter):
    """Deterministic keyword search over a tiny in-memory corpus."""

    name = "mock-search"

    def search(self, query: str, limit: int = 10) -> list[Evidence]:
        terms = {t.lower() for t in query.split() if len(t) > 3}
        scored = []
        for kind, source, claim, strength in _CORPUS:
            overlap = sum(1 for t in terms if t in claim.lower() or t in source.lower())
            scored.append((overlap, kind, source, claim, strength))
        scored.sort(key=lambda r: -r[0])
        return [
            Evidence(kind=k, source=s, claim=c, strength=st, meta={"match_score": score})
            for score, k, s, c, st in scored[:limit]
        ]


class MockExperimentAdapter(ExperimentAdapter):
    """Simulates an experiment by sampling from a hidden ground-truth hypothesis.

    The agent is never told which hypothesis is true. It has to find out — which
    is precisely the thing we are claiming it can do.
    """

    name = "mock-lab"

    def __init__(self, truth_hypothesis_id: str | None = None, seed: int = 1729):
        self.truth = truth_hypothesis_id
        self.rng = random.Random(seed)

    def run(self, experiment: Experiment) -> Observation:
        likelihoods = experiment.normalised_likelihoods()
        row = likelihoods.get(self.truth or "") if self.truth else None
        if row is None:
            # No ground truth configured: sample uniformly over outcomes.
            labels = [o.label for o in experiment.outcomes]
            weights = [1.0] * len(labels)
        else:
            labels = list(row.keys())
            weights = list(row.values())
        label = self.rng.choices(labels, weights=weights, k=1)[0]
        return Observation(
            experiment_id=experiment.id,
            outcome_label=label,
            raw={
                "simulated": True,
                "truth": self.truth,
                "weights": dict(zip(labels, weights, strict=True)),
            },
            source=self.name,
            held_out=True,
        )


class ScriptedExperimentAdapter(ExperimentAdapter):
    """Replays a fixed sequence of outcomes.

    This is the workhorse of the counterfactual harness: run the identical agent
    against two scripted worlds and diff what it proposes next.
    """

    name = "scripted-lab"

    def __init__(self, outcomes: list[str]):
        self.outcomes = list(outcomes)
        self._i = 0

    def run(self, experiment: Experiment) -> Observation:
        valid = [o.label for o in experiment.outcomes]
        label = self.outcomes[self._i] if self._i < len(self.outcomes) else valid[0]
        self._i += 1
        if label not in valid:
            # The script named an outcome this experiment cannot produce; fall
            # back to the first valid one rather than corrupting the update.
            label = valid[0]
        return Observation(
            experiment_id=experiment.id,
            outcome_label=label,
            raw={"scripted": True, "index": self._i - 1},
            source=self.name,
            held_out=True,
        )
