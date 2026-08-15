"""Adapter interface.

Every external tool — Paperclip, Proto, ESM on Modal, Tamarind, Benchling —
enters the system through one of two verbs:

    search(query)  -> Evidence   (things we can read)
    run(experiment) -> Observation (things we can do)

Keeping the surface this narrow is what lets the same agent loop drive a
literature meta-analysis on Saturday and a protein design pipeline on Sunday
without rewriting the reasoning layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from probception.types import Evidence, Experiment, Observation


class SearchAdapter(ABC):
    """A source of evidence."""

    name: str = "abstract-search"

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[Evidence]:
        """Return evidence matching the query. Must be safe to call offline."""

    def available(self) -> bool:
        return True


class ExperimentAdapter(ABC):
    """A thing that can execute a proposed experiment."""

    name: str = "abstract-experiment"

    @abstractmethod
    def run(self, experiment: Experiment) -> Observation:
        """Execute and return exactly one observed outcome label."""

    def available(self) -> bool:
        return True


class AdapterError(RuntimeError):
    """Raised when a live adapter is asked to work without credentials."""
