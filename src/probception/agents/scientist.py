"""The reasoning layer: turn a question into hypotheses, and hypotheses into
candidate experiments.

Every method here has two implementations behind one interface:

  * `LLMScientist`        — Claude proposes hypotheses and experiments.
  * `HeuristicScientist`  — a deterministic stand-in that needs no API key.

The heuristic path is not a placeholder to be deleted. It is the control arm:
running the same loop with reasoning swapped out tells you how much of the
result came from the model versus from the Bayesian machinery underneath.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel

from probception.agents.llm import Claude
from probception.types import Evidence, Experiment, Hypothesis, Outcome

SYSTEM = """You are the reasoning core of Probception, an AI scientist.

You do not give answers. You maintain explicit, numerical beliefs and you design
the experiment most likely to prove yourself wrong.

Rules you never break:
1. Every hypothesis must be falsifiable — state it so that some observable
   result would make it less likely.
2. Every hypothesis carries a prior in [0,1]; priors across the set sum to 1.
3. Every claim cites evidence by id from the evidence list you were given. If
   you have no evidence for something, say so and lower its prior.
4. Every experiment you propose specifies P(outcome | hypothesis) for every
   hypothesis and every outcome. Each hypothesis's row sums to 1.
5. A good experiment is one whose outcome you cannot already predict. If every
   hypothesis predicts the same result, the experiment is worthless — do not
   propose it.
6. Prefer cheap experiments that discriminate strongly over expensive ones that
   discriminate weakly. State cost honestly on a 1-10 relative scale.

Write for a scientist who will have to defend this to a reviewer."""


class HypothesisSet(BaseModel):
    """Container the model fills in one shot."""

    hypotheses: list[Hypothesis]
    reasoning: str = ""


class ExperimentSet(BaseModel):
    experiments: list[Experiment]
    reasoning: str = ""


class Scientist(ABC):
    """Interface used by the loop."""

    name: str = "abstract"

    @abstractmethod
    def hypothesise(self, question: str, evidence: list[Evidence]) -> list[Hypothesis]: ...

    @abstractmethod
    def design(
        self, question: str, hypotheses: list[Hypothesis], evidence: list[Evidence], n: int = 4
    ) -> list[Experiment]: ...


class LLMScientist(Scientist):
    """Claude-backed reasoning."""

    name = "claude"

    def __init__(self, claude: Claude):
        self.claude = claude

    def hypothesise(self, question: str, evidence: list[Evidence]) -> list[Hypothesis]:
        user = (
            f"# Research question\n{question}\n\n"
            f"# Evidence available\n{_render_evidence(evidence)}\n\n"
            "Propose 3-5 competing, mutually exclusive hypotheses that between them "
            "cover the plausible answer space. Assign priors that sum to 1.0 and "
            "justify each with evidence ids."
        )
        result = self.claude.structured(
            system=SYSTEM, user=user, schema=HypothesisSet, label="hypothesise"
        )
        return _renormalise(result.hypotheses)

    def design(
        self, question: str, hypotheses: list[Hypothesis], evidence: list[Evidence], n: int = 4
    ) -> list[Experiment]:
        user = (
            f"# Research question\n{question}\n\n"
            f"# Current hypotheses (with ids you MUST reuse verbatim)\n"
            f"{_render_hypotheses(hypotheses)}\n\n"
            f"# Evidence available\n{_render_evidence(evidence)}\n\n"
            f"Design {n} candidate experiments. For each, give 2-4 discrete outcomes and "
            "a full likelihood table: for every hypothesis id above, P(outcome|hypothesis) "
            "over those outcomes, summing to 1. Make the experiments genuinely different "
            "from each other — they should discriminate between different pairs of hypotheses."
        )
        result = self.claude.structured(
            system=SYSTEM, user=user, schema=ExperimentSet, label="design", max_tokens=20000
        )
        valid_ids = {h.id for h in hypotheses}
        return [e for e in result.experiments if _covers(e, valid_ids)]


class HeuristicScientist(Scientist):
    """Deterministic reasoning. No API key, no network, always the same answer.

    Generates a hypothesis set spanning "strong effect / weak effect / no effect
    / confounded" — the four shapes most empirical questions actually collapse
    into — and builds discriminating assays over them.
    """

    name = "heuristic"

    def hypothesise(self, question: str, evidence: list[Evidence]) -> list[Hypothesis]:
        ev_ids = [e.id for e in evidence[:3]]
        frames = [
            ("The effect is real and large enough to act on.", 0.30),
            ("The effect is real but too small to matter in practice.", 0.30),
            ("There is no effect; prior reports are noise.", 0.25),
            ("The apparent effect is driven by a confounder.", 0.15),
        ]
        return _renormalise(
            [
                Hypothesis(
                    statement=f"{s} (re: {question})",
                    rationale="Baseline decomposition of the effect space.",
                    prior=p,
                    evidence_ids=ev_ids,
                )
                for s, p in frames
            ]
        )

    def design(
        self, question: str, hypotheses: list[Hypothesis], evidence: list[Evidence], n: int = 4
    ) -> list[Experiment]:
        ids = [h.id for h in hypotheses]
        specs = [
            ("High-power replication", "Repeat the primary measurement at 5x sample size.", 3.0,
             [0.85, 0.55, 0.10, 0.45]),
            ("Dose-response series", "Measure across a 5-point concentration ladder.", 4.0,
             [0.90, 0.40, 0.08, 0.30]),
            ("Negative control panel", "Run the assay against scrambled/inactive inputs.", 1.0,
             [0.60, 0.55, 0.15, 0.80]),
            ("Orthogonal readout", "Re-measure with a method that shares no failure mode.", 5.0,
             [0.88, 0.45, 0.05, 0.20]),
        ]
        experiments = []
        for title, protocol, cost, hit_rates in specs[:n]:
            # strict=False: the hypothesis count is whatever the reasoner produced,
            # so pair against as many hit-rates as we have and let extras fall away.
            likelihoods = {
                hid: {"positive": hit, "negative": 1.0 - hit}
                for hid, hit in zip(ids, hit_rates, strict=False)
            }
            experiments.append(
                Experiment(
                    title=title,
                    protocol=protocol,
                    outcomes=[
                        Outcome(label="positive", description="Signal detected above threshold."),
                        Outcome(label="negative", description="No signal above threshold."),
                    ],
                    likelihoods=likelihoods,
                    cost=cost,
                    tool="mock",
                )
            )
        return experiments


# -- helpers -------------------------------------------------------------
def _renormalise(hypotheses: list[Hypothesis]) -> list[Hypothesis]:
    total = sum(h.prior for h in hypotheses) or 1.0
    for h in hypotheses:
        h.prior = h.prior / total
        h.posterior = h.prior
    return hypotheses


def _covers(experiment: Experiment, hypothesis_ids: set[str]) -> bool:
    """Drop experiments that do not give a likelihood row for every hypothesis."""
    return hypothesis_ids.issubset(set(experiment.likelihoods.keys()))


def _render_evidence(evidence: list[Evidence]) -> str:
    if not evidence:
        return "(none retrieved)"
    return "\n".join(
        f"- [{e.id}] ({e.kind.value}, {e.source}, strength={e.strength:.2f}) {e.claim}"
        for e in evidence
    )


def _render_hypotheses(hypotheses: list[Hypothesis]) -> str:
    return "\n".join(f"- [{h.id}] p={h.p:.3f} — {h.statement}" for h in hypotheses)
