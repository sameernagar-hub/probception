"""Proto adapter — generative biological design as an *experiment*.

The framing matters. Probception does not treat a design run as "generate some
sequences"; it treats it as an experiment with discrete, pre-declared outcomes
(`hit`, `weak`, `miss`) whose likelihoods under each hypothesis were written down
*before* the job was submitted. That is what makes a design campaign scoreable
instead of merely impressive.

Wire up `_submit` to the Proto endpoint from the credits slide and the rest of
the loop needs no changes.
"""

from __future__ import annotations

from typing import Any

import httpx

from probception.adapters.base import AdapterError, ExperimentAdapter
from probception.config import settings
from probception.types import Experiment, Observation


class ProtoAdapter(ExperimentAdapter):
    name = "proto"

    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 600.0):
        self.api_key = api_key or settings.proto_api_key
        self.base_url = (base_url or settings.proto_base_url or "").rstrip("/")
        self.timeout = timeout

    def available(self) -> bool:
        return bool(self.api_key and self.base_url)

    def run(self, experiment: Experiment) -> Observation:
        if not self.available():
            raise AdapterError(
                "Proto is not configured. Set PROTO_API_KEY and PROTO_BASE_URL from the "
                "Proto credits slide, or run with PROBCEPTION_MODE=mock."
            )
        body = self._submit(experiment)
        label = self._classify(body, experiment)
        return Observation(
            experiment_id=experiment.id,
            outcome_label=label,
            raw=body,
            source=self.name,
            held_out=True,
        )

    def _submit(self, experiment: Experiment) -> dict[str, Any]:
        payload = {
            "objective": experiment.title,
            "spec": experiment.protocol,
            **experiment.params,
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/v1/design",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    def _classify(self, body: dict[str, Any], experiment: Experiment) -> str:
        """Map a continuous design score onto the experiment's declared outcomes.

        Thresholds live in `experiment.params` so they are recorded in the ledger
        before the job runs — you cannot move the goalposts after seeing results.
        """
        valid = [o.label for o in experiment.outcomes]
        score = float(body.get("best_score", body.get("score", 0.0)) or 0.0)
        hit = float(experiment.params.get("hit_threshold", 0.8))
        weak = float(experiment.params.get("weak_threshold", 0.5))

        if score >= hit and "hit" in valid:
            return "hit"
        if score >= weak and "weak" in valid:
            return "weak"
        if "miss" in valid:
            return "miss"
        return valid[-1]
