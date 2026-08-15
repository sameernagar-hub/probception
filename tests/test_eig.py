"""Information-gain scoring. If this is wrong, the agent picks the wrong experiments."""

from __future__ import annotations

import pytest

from probception.belief.state import BeliefState
from probception.design.eig import choose, expected_information_gain, rank
from probception.types import Experiment, Hypothesis, Outcome


def belief() -> BeliefState:
    return BeliefState(
        [
            Hypothesis(statement="A", prior=0.5),
            Hypothesis(statement="B", prior=0.5),
        ]
    )


def experiment(rows: list[dict[str, float]], cost: float = 1.0, title: str = "e") -> Experiment:
    ids = list(belief().as_dict().keys())
    return Experiment(
        title=title,
        protocol="p",
        outcomes=[Outcome(label="positive"), Outcome(label="negative")],
        likelihoods=dict(zip(ids, rows, strict=True)),
        cost=cost,
    )


def test_perfectly_discriminating_experiment_resolves_one_bit():
    b = belief()
    # A always positive, B always negative: one coin flip fully resolved.
    perfect = experiment([{"positive": 1.0, "negative": 0.0}, {"positive": 0.0, "negative": 1.0}])
    score = expected_information_gain(b, perfect)
    assert score.eig == pytest.approx(1.0, abs=1e-6)


def test_uninformative_experiment_scores_zero():
    b = belief()
    useless = experiment([{"positive": 0.5, "negative": 0.5}, {"positive": 0.5, "negative": 0.5}])
    assert expected_information_gain(b, useless).eig == pytest.approx(0.0, abs=1e-9)


def test_eig_is_never_negative():
    b = belief()
    for rows in (
        [{"positive": 0.9, "negative": 0.1}, {"positive": 0.85, "negative": 0.15}],
        [{"positive": 0.01, "negative": 0.99}, {"positive": 0.99, "negative": 0.01}],
    ):
        assert expected_information_gain(b, experiment(rows)).eig >= 0.0


def test_cost_breaks_ties_toward_the_cheaper_experiment():
    b = belief()
    rows = [{"positive": 1.0, "negative": 0.0}, {"positive": 0.0, "negative": 1.0}]
    cheap = experiment(rows, cost=1.0, title="cheap")
    pricey = experiment(rows, cost=10.0, title="pricey")
    winner, _ = choose(b, [pricey, cheap])
    assert winner.experiment.title == "cheap"


def test_ranking_prefers_the_more_discriminating_experiment_at_equal_cost():
    b = belief()
    strong = experiment(
        [{"positive": 0.95, "negative": 0.05}, {"positive": 0.05, "negative": 0.95}],
        title="strong",
    )
    weak = experiment(
        [{"positive": 0.55, "negative": 0.45}, {"positive": 0.45, "negative": 0.55}],
        title="weak",
    )
    ordered = rank(b, [weak, strong])
    assert ordered[0].experiment.title == "strong"
    assert ordered[0].eig > ordered[1].eig


def test_repeating_an_experiment_is_worth_less_than_the_first_run():
    b = belief()
    rows = [{"positive": 0.9, "negative": 0.1}, {"positive": 0.2, "negative": 0.8}]
    e = experiment(rows)
    first = expected_information_gain(b, e, times_run=0)
    second = expected_information_gain(b, e, times_run=1)
    third = expected_information_gain(b, e, times_run=2)

    # Raw information content is unchanged — only its novelty-adjusted value drops.
    assert second.eig == pytest.approx(first.eig)
    assert second.utility < first.utility
    assert third.utility < second.utility


def test_planner_moves_on_rather_than_repeating_the_cheapest_assay():
    """The failure this guards against: an agent that runs one cheap test forever.

    Costs are chosen so the tradeoff genuinely flips. `cheap` yields ~0.066 bits
    at cost 1 (utility 0.066); `thorough` yields ~0.714 bits at cost 15 (utility
    0.048). So `cheap` wins while it is still novel — but after two runs its
    novelty discount (0.45^2) drops its utility to ~0.013 and `thorough` wins.
    """
    b = belief()
    cheap = experiment(
        [{"positive": 0.7, "negative": 0.3}, {"positive": 0.4, "negative": 0.6}],
        cost=1.0,
        title="cheap",
    )
    thorough = experiment(
        [{"positive": 0.95, "negative": 0.05}, {"positive": 0.05, "negative": 0.95}],
        cost=15.0,
        title="thorough",
    )

    fresh, _ = choose(b, [cheap, thorough], history={})
    assert fresh.experiment.title == "cheap", "cheap wins on first pass"

    after_repeats, _ = choose(b, [cheap, thorough], history={cheap.id: 2})
    assert after_repeats.experiment.title == "thorough", (
        "after running the cheap assay twice the planner must switch"
    )


def test_choose_rejects_an_empty_candidate_set():
    with pytest.raises(ValueError):
        choose(belief(), [])


def test_outcome_posteriors_are_distributions():
    score = expected_information_gain(
        belief(),
        experiment([{"positive": 0.8, "negative": 0.2}, {"positive": 0.3, "negative": 0.7}]),
    )
    for posterior in score.outcome_posteriors.values():
        assert sum(posterior.values()) == pytest.approx(1.0)
