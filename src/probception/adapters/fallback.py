"""Deterministic fallbacks for live integrations.

Partner tools should make Probception better when they work, not make the demo
fragile when they do not. These wrappers keep live failures inside the adapter
boundary and degrade to deterministic mock behavior with the failure reason
preserved in returned metadata.
"""

from __future__ import annotations

from probception.adapters.base import ExperimentAdapter, SearchAdapter
from probception.adapters.mock import MockExperimentAdapter, MockSearchAdapter
from probception.types import Evidence, Experiment, Observation


class ResilientSearchAdapter(SearchAdapter):
    """Try a live searcher, then fall back to deterministic mock evidence."""

    def __init__(
        self,
        primary: SearchAdapter,
        fallback: SearchAdapter | None = None,
    ):
        self.primary = primary
        self.fallback = fallback or MockSearchAdapter()
        self.name = f"{primary.name}-with-fallback"

    def available(self) -> bool:
        return True

    def search(self, query: str, limit: int = 10) -> list[Evidence]:
        try:
            evidence = self.primary.search(query, limit=limit)
            if evidence:
                return evidence
            reason = "primary returned no evidence"
        except Exception as exc:  # noqa: BLE001 - failures are converted to evidence metadata.
            reason = f"{type(exc).__name__}: {exc}"
        fallback = self.fallback.search(query, limit=limit)
        for item in fallback:
            item.meta["fallback_from"] = self.primary.name
            item.meta["fallback_reason"] = reason
        return fallback


class ResilientExperimentAdapter(ExperimentAdapter):
    """Try a live experiment adapter, then run a deterministic local lab."""

    def __init__(
        self,
        primary: ExperimentAdapter,
        fallback: ExperimentAdapter | None = None,
    ):
        self.primary = primary
        self.fallback = fallback or MockExperimentAdapter()
        self.name = f"{primary.name}-with-fallback"

    def available(self) -> bool:
        return True

    def run(self, experiment: Experiment) -> Observation:
        try:
            observation = self.primary.run(experiment)
            if observation.outcome_label in {outcome.label for outcome in experiment.outcomes}:
                return observation
            reason = f"primary returned undeclared outcome {observation.outcome_label!r}"
        except Exception as exc:  # noqa: BLE001 - fallback is the whole point of this adapter.
            reason = f"{type(exc).__name__}: {exc}"
        observation = self.fallback.run(experiment)
        observation.raw["fallback_from"] = self.primary.name
        observation.raw["fallback_reason"] = reason
        observation.source = f"{self.fallback.name}-fallback"
        return observation
