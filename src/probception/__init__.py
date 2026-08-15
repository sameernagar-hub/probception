"""Probception — an AI scientist that shows its work as probabilities.

It states what it believes, how sure it is, and runs the experiment most likely
to prove itself wrong.
"""

__version__ = "0.1.0"

from probception.belief import BeliefState
from probception.config import settings
from probception.design import choose, expected_information_gain
from probception.loop import ClosedLoop
from probception.trace import Ledger, write_report
from probception.types import (
    Decision,
    Evidence,
    Experiment,
    Hypothesis,
    Observation,
    Outcome,
    RunSummary,
)

__all__ = [
    "BeliefState",
    "ClosedLoop",
    "Decision",
    "Evidence",
    "Experiment",
    "Hypothesis",
    "Ledger",
    "Observation",
    "Outcome",
    "RunSummary",
    "__version__",
    "choose",
    "expected_information_gain",
    "settings",
    "write_report",
]
