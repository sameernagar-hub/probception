"""Typed contracts shared by every layer of Probception.

Everything the agent believes, proposes, or observes is one of these objects.
They are all Pydantic models so that (a) the LLM can emit them directly via
structured outputs and (b) any run can be serialised to the ledger and replayed
byte-for-byte.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


def _now() -> str:
    return datetime.now(UTC).isoformat()


def content_id(payload: Any, prefix: str) -> str:
    """Content-addressed id. Same content -> same id, always.

    This is what makes provenance checkable rather than merely claimed: an
    evidence id is a hash of the evidence, so a citation cannot drift from the
    thing it cites.
    """
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return f"{prefix}_{hashlib.sha256(blob).hexdigest()[:16]}"


class SourceKind(StrEnum):
    PAPER = "paper"
    DATASET = "dataset"
    CLINICAL_TRIAL = "clinical_trial"
    DATABASE = "database"
    ASSAY = "assay"
    MODEL_PREDICTION = "model_prediction"
    PRIOR_RUN = "prior_run"


class Evidence(BaseModel):
    """One retrievable, quotable fact. Every claim must cite at least one."""

    id: str = ""
    kind: SourceKind
    source: str = Field(description="Where this came from: DOI, accession, URL, tool name.")
    claim: str = Field(description="The single fact, in one sentence.")
    quote: str | None = Field(default=None, description="Verbatim supporting span, if any.")
    strength: float = Field(
        default=0.5, ge=0.0, le=1.0, description="How much weight this evidence deserves."
    )
    retrieved_at: str = Field(default_factory=_now)
    meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _assign_id(self) -> Evidence:
        if not self.id:
            object.__setattr__(
                self,
                "id",
                content_id({"kind": self.kind, "source": self.source, "claim": self.claim}, "ev"),
            )
        return self


class Hypothesis(BaseModel):
    """A candidate explanation carrying an explicit probability."""

    id: str = ""
    statement: str = Field(description="A falsifiable claim, stated so it could be wrong.")
    rationale: str = Field(default="", description="Why this is on the table at all.")
    prior: float = Field(ge=0.0, le=1.0)
    posterior: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _assign_id(self) -> Hypothesis:
        if not self.id:
            object.__setattr__(self, "id", content_id({"s": self.statement}, "hyp"))
        if self.posterior is None:
            object.__setattr__(self, "posterior", self.prior)
        return self

    @property
    def p(self) -> float:
        """Current credence — posterior if we have one, else the prior."""
        return self.posterior if self.posterior is not None else self.prior


class Outcome(BaseModel):
    """A discrete result an experiment could produce."""

    label: str = Field(description="Short machine-friendly name, e.g. 'binds' or 'no_change'.")
    description: str = ""


class Experiment(BaseModel):
    """A proposed next step, with a likelihood model that makes it scoreable.

    `likelihoods[hypothesis_id][outcome_label]` is P(outcome | hypothesis).
    Each hypothesis's row must sum to 1. That constraint is what turns a vague
    "we should try X" into something whose information value can be computed.
    """

    id: str = ""
    title: str
    protocol: str = Field(description="What is actually done, concretely enough to run.")
    outcomes: list[Outcome]
    likelihoods: dict[str, dict[str, float]]
    cost: float = Field(default=1.0, gt=0.0, description="Relative cost: time, reagents, compute.")
    tool: str = Field(default="mock", description="Adapter that executes this: proto, esm, ...")
    params: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _assign_id(self) -> Experiment:
        if not self.id:
            object.__setattr__(self, "id", content_id({"t": self.title, "p": self.protocol}, "exp"))
        return self

    @field_validator("outcomes")
    @classmethod
    def _needs_two_outcomes(cls, v: list[Outcome]) -> list[Outcome]:
        if len(v) < 2:
            raise ValueError("An experiment with fewer than 2 outcomes cannot be informative.")
        return v

    def normalised_likelihoods(self) -> dict[str, dict[str, float]]:
        """Row-normalise, tolerating small LLM arithmetic slips."""
        labels = [o.label for o in self.outcomes]
        out: dict[str, dict[str, float]] = {}
        for hyp_id, row in self.likelihoods.items():
            vals = {lbl: max(float(row.get(lbl, 0.0)), 1e-9) for lbl in labels}
            total = sum(vals.values())
            out[hyp_id] = {lbl: v / total for lbl, v in vals.items()}
        return out


class Observation(BaseModel):
    """What actually came back when the experiment ran."""

    experiment_id: str
    outcome_label: str
    raw: dict[str, Any] = Field(default_factory=dict)
    source: str = "mock"
    observed_at: str = Field(default_factory=_now)
    held_out: bool = Field(
        default=True, description="True when the agent had never seen this before deciding."
    )


class Decision(BaseModel):
    """One inspectable step of reasoning: why this experiment, over what else."""

    step: int
    chosen_experiment_id: str
    expected_information_gain: float
    utility: float
    considered: list[dict[str, Any]] = Field(
        default_factory=list, description="Every candidate scored, not just the winner."
    )
    belief_before: dict[str, float]
    belief_after: dict[str, float] | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    reasoning: str = ""
    made_at: str = Field(default_factory=_now)


class RunSummary(BaseModel):
    """The end state of a closed loop."""

    run_id: str
    question: str
    steps: int
    final_belief: dict[str, float]
    leading_hypothesis: str
    entropy_start: float
    entropy_end: float
    next_experiment: str | None = None
    ledger_path: str = ""
    report_path: str = ""
