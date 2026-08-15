"""The belief layer is the part we can prove correct, so it gets real tests."""

from __future__ import annotations

import math

import pytest

from probception.belief.state import BeliefState, entropy, normalise
from probception.types import Experiment, Hypothesis, Observation, Outcome


def make_belief() -> BeliefState:
    return BeliefState(
        [
            Hypothesis(statement="A is true", prior=0.5),
            Hypothesis(statement="B is true", prior=0.3),
            Hypothesis(statement="C is true", prior=0.2),
        ]
    )


def make_experiment(belief: BeliefState, discriminating: bool = True) -> Experiment:
    ids = list(belief.as_dict().keys())
    if discriminating:
        rows = [
            {"positive": 0.9, "negative": 0.1},
            {"positive": 0.5, "negative": 0.5},
            {"positive": 0.1, "negative": 0.9},
        ]
    else:
        rows = [{"positive": 0.5, "negative": 0.5}] * 3
    return Experiment(
        title="assay",
        protocol="run it",
        outcomes=[Outcome(label="positive"), Outcome(label="negative")],
        likelihoods=dict(zip(ids, rows, strict=True)),
    )


def test_entropy_is_maximal_for_uniform():
    uniform = {"a": 0.25, "b": 0.25, "c": 0.25, "d": 0.25}
    assert entropy(uniform) == pytest.approx(2.0)
    assert entropy({"a": 1.0}) == pytest.approx(0.0)


def test_normalise_handles_degenerate_input():
    assert sum(normalise({"a": 0.0, "b": 0.0}).values()) == pytest.approx(1.0)
    assert normalise({"a": 2.0, "b": 2.0}) == {"a": 0.5, "b": 0.5}


def test_priors_are_normalised_on_construction():
    # Individually valid probabilities that do not sum to 1 — the common case
    # when a language model assigns priors independently.
    belief = BeliefState(
        [Hypothesis(statement="x", prior=0.8), Hypothesis(statement="y", prior=0.8)]
    )
    assert sum(belief.as_dict().values()) == pytest.approx(1.0)
    assert all(p == pytest.approx(0.5) for p in belief.as_dict().values())


def test_out_of_range_priors_are_rejected_at_the_boundary():
    with pytest.raises(ValueError):
        Hypothesis(statement="impossible", prior=2.0)


def test_bayes_update_moves_toward_the_supported_hypothesis():
    belief = make_belief()
    experiment = make_experiment(belief)
    ids = list(belief.as_dict().keys())
    before = belief.as_dict()

    belief.update(experiment, Observation(experiment_id=experiment.id, outcome_label="positive"))
    after = belief.as_dict()

    # The hypothesis that predicted "positive" most strongly must gain.
    assert after[ids[0]] > before[ids[0]]
    # The one that predicted it least must lose.
    assert after[ids[2]] < before[ids[2]]
    assert sum(after.values()) == pytest.approx(1.0)


def test_uninformative_experiment_leaves_belief_untouched():
    belief = make_belief()
    experiment = make_experiment(belief, discriminating=False)
    before = belief.as_dict()
    belief.update(experiment, Observation(experiment_id=experiment.id, outcome_label="positive"))
    after = belief.as_dict()
    for key in before:
        assert after[key] == pytest.approx(before[key])


def test_predicted_outcomes_form_a_distribution():
    belief = make_belief()
    predicted = belief.predict_outcome(make_experiment(belief))
    assert sum(predicted.values()) == pytest.approx(1.0)
    assert all(0.0 <= p <= 1.0 for p in predicted.values())


def test_surprise_is_higher_for_the_less_expected_outcome():
    belief = make_belief()
    experiment = make_experiment(belief)
    predicted = belief.predict_outcome(experiment)
    likely = max(predicted, key=lambda k: predicted[k])
    unlikely = min(predicted, key=lambda k: predicted[k])

    s_likely = belief.surprise(experiment, Observation(experiment_id="e", outcome_label=likely))
    s_unlikely = belief.surprise(experiment, Observation(experiment_id="e", outcome_label=unlikely))
    assert s_unlikely > s_likely
    assert math.isfinite(s_likely)


def test_likelihood_rows_are_renormalised():
    belief = make_belief()
    ids = list(belief.as_dict().keys())
    experiment = Experiment(
        title="sloppy",
        protocol="rows that do not sum to 1",
        outcomes=[Outcome(label="yes"), Outcome(label="no")],
        likelihoods={hid: {"yes": 3.0, "no": 1.0} for hid in ids},
    )
    for row in experiment.normalised_likelihoods().values():
        assert sum(row.values()) == pytest.approx(1.0)


def test_experiment_requires_two_outcomes():
    with pytest.raises(ValueError):
        Experiment(
            title="pointless",
            protocol="one possible result",
            outcomes=[Outcome(label="only")],
            likelihoods={},
        )
