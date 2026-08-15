"""Bayesian optimal experimental design.

Score every candidate experiment by how much it would change the agent's mind,
then pick the best one per unit of cost. This is the module that makes the
agent's choice of "what next" a computation rather than a vibe.
"""

from __future__ import annotations

from dataclasses import dataclass

from probception.belief.state import BeliefState, entropy, normalise
from probception.types import Experiment

EPS = 1e-12


@dataclass
class Score:
    experiment: Experiment
    eig: float
    """Expected information gain, in bits."""
    utility: float
    """EIG discounted by cost and by repetition — what we actually rank on."""
    outcome_posteriors: dict[str, dict[str, float]]
    """What the belief would become under each possible outcome."""
    predicted_outcomes: dict[str, float]
    """The agent's prediction, recorded before anything runs."""
    times_run: int = 0
    """How often this experiment has already been executed in this run."""
    novelty: float = 1.0
    """Discount applied for repetition. 1.0 means never run before."""

    def explain(self) -> str:
        top = max(self.predicted_outcomes.items(), key=lambda kv: kv[1])
        repeat = (
            f" Already run {self.times_run}x, so its information is discounted "
            f"to {self.novelty:.2f} of face value."
            if self.times_run
            else ""
        )
        return (
            f"{self.experiment.title}: expected to resolve {self.eig:.3f} bits "
            f"at cost {self.experiment.cost:.2f} (utility {self.utility:.3f}). "
            f"Most likely outcome: '{top[0]}' at p={top[1]:.2f}.{repeat}"
        )


def novelty_discount(times_run: int, decay: float = 0.45) -> float:
    """How much *new* information a repeat of the same experiment is worth.

    The EIG formula assumes each observation is conditionally independent given
    the hypothesis. For a repeated run of the *same* protocol that is false:
    systematic error, batch effects and a fixed reagent lot are shared, so the
    second run tells you materially less than the first. Without this term the
    planner degenerates into running the single cheapest assay forever, which is
    both bad science and a bad demo.

    decay=0.45 means a second run is worth ~45% of the first, a third ~20%.
    """
    return decay**times_run


def expected_information_gain(
    belief: BeliefState,
    experiment: Experiment,
    times_run: int = 0,
) -> Score:
    """EIG = H(prior) - E_outcome[ H(posterior | outcome) ].

    Read plainly: how many bits of uncertainty do we expect this experiment to
    remove? An experiment whose result we can already predict scores ~0, no
    matter how impressive it looks.
    """
    prior = belief.as_dict()
    h_prior = entropy(prior)
    likelihoods = experiment.normalised_likelihoods()
    predicted = belief.predict_outcome(experiment)

    expected_posterior_entropy = 0.0
    outcome_posteriors: dict[str, dict[str, float]] = {}

    for outcome in experiment.outcomes:
        label = outcome.label
        unnormalised = {
            hid: p_h * likelihoods.get(hid, {}).get(label, EPS) for hid, p_h in prior.items()
        }
        posterior = normalise(unnormalised)
        outcome_posteriors[label] = posterior
        expected_posterior_entropy += predicted.get(label, 0.0) * entropy(posterior)

    eig = max(h_prior - expected_posterior_entropy, 0.0)
    novelty = novelty_discount(times_run)
    utility = (eig * novelty) / max(experiment.cost, EPS)

    return Score(
        experiment=experiment,
        eig=eig,
        utility=utility,
        outcome_posteriors=outcome_posteriors,
        predicted_outcomes=predicted,
        times_run=times_run,
        novelty=novelty,
    )


def rank(
    belief: BeliefState,
    candidates: list[Experiment],
    history: dict[str, int] | None = None,
) -> list[Score]:
    """Score every candidate, best utility first.

    `history` maps experiment id -> how many times it has already been run in
    this investigation, so repeats are discounted.
    """
    history = history or {}
    scores = [
        expected_information_gain(belief, e, times_run=history.get(e.id, 0)) for e in candidates
    ]
    return sorted(scores, key=lambda s: s.utility, reverse=True)


def choose(
    belief: BeliefState,
    candidates: list[Experiment],
    history: dict[str, int] | None = None,
) -> tuple[Score, list[Score]]:
    """Pick the most informative affordable experiment. Returns (winner, all)."""
    if not candidates:
        raise ValueError("No candidate experiments to choose from.")
    scored = rank(belief, candidates, history)
    return scored[0], scored
