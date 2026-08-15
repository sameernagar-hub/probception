"""The belief state: a probability distribution over hypotheses, and Bayes.

This module is deliberately dependency-light and fully deterministic. It is the
part of the system whose correctness we can actually prove, so it holds no LLM
calls and no I/O.
"""

from __future__ import annotations

import math

from probception.types import Experiment, Hypothesis, Observation

EPS = 1e-12


def entropy(dist: dict[str, float]) -> float:
    """Shannon entropy in bits. High entropy == the agent does not know yet."""
    return -sum(p * math.log2(p) for p in dist.values() if p > EPS)


def normalise(dist: dict[str, float]) -> dict[str, float]:
    total = sum(max(v, 0.0) for v in dist.values())
    if total <= EPS:
        n = len(dist)
        return {k: 1.0 / n for k in dist}
    return {k: max(v, 0.0) / total for k, v in dist.items()}


class BeliefState:
    """A first-class, serialisable set of beliefs over competing hypotheses."""

    def __init__(self, hypotheses: list[Hypothesis]):
        if not hypotheses:
            raise ValueError("A belief state needs at least one hypothesis.")
        self.hypotheses: dict[str, Hypothesis] = {h.id: h for h in hypotheses}
        self._p: dict[str, float] = normalise({h.id: h.prior for h in hypotheses})
        self._sync()

    # -- access ----------------------------------------------------------
    def as_dict(self) -> dict[str, float]:
        return dict(self._p)

    def labelled(self) -> dict[str, float]:
        """Belief keyed by human-readable statement — for reports and demos."""
        return {self.hypotheses[hid].statement: p for hid, p in self._p.items()}

    @property
    def entropy(self) -> float:
        return entropy(self._p)

    def leader(self) -> Hypothesis:
        best = max(self._p.items(), key=lambda kv: kv[1])[0]
        return self.hypotheses[best]

    def _sync(self) -> None:
        for hid, p in self._p.items():
            self.hypotheses[hid].posterior = p

    # -- inference -------------------------------------------------------
    def predict_outcome(self, experiment: Experiment) -> dict[str, float]:
        """Marginal P(outcome) = sum_h P(h) * P(outcome | h).

        This is the agent's *prediction*. Recording it before the result arrives
        is what makes the run scoreable after the fact.
        """
        likelihoods = experiment.normalised_likelihoods()
        marginal = {o.label: 0.0 for o in experiment.outcomes}
        for hid, p_h in self._p.items():
            row = likelihoods.get(hid)
            if not row:
                continue
            for label, p_o_given_h in row.items():
                marginal[label] += p_h * p_o_given_h
        return normalise(marginal)

    def update(self, experiment: Experiment, observation: Observation) -> dict[str, float]:
        """Bayes. Returns the new posterior and mutates the state.

        P(h | o) proportional to P(o | h) * P(h)
        """
        likelihoods = experiment.normalised_likelihoods()
        label = observation.outcome_label
        posterior = {}
        for hid, p_h in self._p.items():
            p_o_given_h = likelihoods.get(hid, {}).get(label, EPS)
            posterior[hid] = p_h * p_o_given_h
        self._p = normalise(posterior)
        self._sync()
        return self.as_dict()

    def surprise(self, experiment: Experiment, observation: Observation) -> float:
        """Bits of surprise: -log2 P(observed outcome) under the prior.

        A high number means the result was one the agent did not expect — which
        is exactly the moment the next proposal ought to change.
        """
        predicted = self.predict_outcome(experiment)
        p = max(predicted.get(observation.outcome_label, EPS), EPS)
        return -math.log2(p)
