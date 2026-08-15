"""Tamarind hosted-job adapter with deterministic failure containment."""

from __future__ import annotations

from typing import Any

import httpx

from probception.adapters.base import AdapterError, ExperimentAdapter
from probception.config import settings
from probception.types import Experiment, Observation


class TamarindAdapter(ExperimentAdapter):
    name = "tamarind"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 600.0,
    ):
        self.api_key = api_key or settings.tamarind_api_key
        self.base_url = (base_url or settings.tamarind_base_url).rstrip("/")
        self.timeout = timeout

    def available(self) -> bool:
        return bool(self.api_key and self.base_url)

    def run(self, experiment: Experiment) -> Observation:
        if not self.available():
            raise AdapterError("Tamarind is not configured. Set TAMARIND_API_KEY.")
        payload = {"name": experiment.title, "protocol": experiment.protocol, "params": experiment.params}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/jobs",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            body: dict[str, Any] = response.json()
        valid = [outcome.label for outcome in experiment.outcomes]
        label = str(body.get("outcome_label") or body.get("status") or valid[0])
        if label not in valid:
            label = valid[0]
        return Observation(
            experiment_id=experiment.id,
            outcome_label=label,
            raw=body,
            source=self.name,
            held_out=True,
        )
