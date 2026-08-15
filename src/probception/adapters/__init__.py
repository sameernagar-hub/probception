"""Adapters: the only places Probception touches the outside world."""

from probception.adapters.base import (
    AdapterError,
    ExperimentAdapter,
    SearchAdapter,
)
from probception.adapters.fallback import ResilientExperimentAdapter, ResilientSearchAdapter
from probception.adapters.mock import (
    MockExperimentAdapter,
    MockSearchAdapter,
    ScriptedExperimentAdapter,
)

__all__ = [
    "AdapterError",
    "ExperimentAdapter",
    "MockExperimentAdapter",
    "MockSearchAdapter",
    "ResilientExperimentAdapter",
    "ResilientSearchAdapter",
    "ScriptedExperimentAdapter",
    "SearchAdapter",
    "get_searcher",
    "get_lab",
]


def get_searcher(mode: str = "mock") -> SearchAdapter:
    """Resolve the evidence source for the current mode."""
    if mode == "live":
        from probception.adapters.paperclip import PaperclipAdapter

        adapter = PaperclipAdapter()
        if adapter.available():
            return ResilientSearchAdapter(adapter, MockSearchAdapter())
    return MockSearchAdapter()


def get_lab(mode: str = "mock", seed: int = 1729) -> ExperimentAdapter:
    """Resolve the experiment executor for the current mode."""
    if mode == "live":
        from probception.adapters.proto import ProtoAdapter

        adapter = ProtoAdapter()
        if adapter.available():
            return ResilientExperimentAdapter(adapter, MockExperimentAdapter(seed=seed))
    return MockExperimentAdapter(seed=seed)
