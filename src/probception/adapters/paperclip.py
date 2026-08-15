"""GXL Paperclip adapter — papers, datasets, clinical trials, biological databases.

Paperclip is our evidence layer. Its job in Probception is not "find me papers"
but "find me things that would move a prior", so every hit is converted into an
`Evidence` object with an explicit strength, and the raw response is retained in
`meta` so a reviewer can go back to the source.

The endpoint shape below is best-effort against the hackathon API. If it drifts,
fix `_ENDPOINT` and `_parse` — everything downstream is insulated from the change.
"""

from __future__ import annotations

from typing import Any

import httpx

from probception.adapters.base import AdapterError, SearchAdapter
from probception.config import settings
from probception.types import Evidence, SourceKind

_ENDPOINT = "/v1/search"

_KIND_MAP = {
    "paper": SourceKind.PAPER,
    "article": SourceKind.PAPER,
    "preprint": SourceKind.PAPER,
    "dataset": SourceKind.DATASET,
    "trial": SourceKind.CLINICAL_TRIAL,
    "clinical_trial": SourceKind.CLINICAL_TRIAL,
    "database": SourceKind.DATABASE,
}


class PaperclipAdapter(SearchAdapter):
    name = "paperclip"

    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 60.0):
        self.api_key = api_key or settings.paperclip_api_key
        self.base_url = (base_url or settings.paperclip_base_url).rstrip("/")
        self.timeout = timeout

    def available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, limit: int = 10) -> list[Evidence]:
        if not self.available():
            raise AdapterError(
                "PAPERCLIP_API_KEY is not set. Create an account at paperclip.gxl.ai/login "
                "and redeem the hackathon code, or run with PROBCEPTION_MODE=mock."
            )
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}{_ENDPOINT}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"query": query, "limit": limit},
            )
            response.raise_for_status()
            return self._parse(response.json(), limit)

    def _parse(self, body: Any, limit: int) -> list[Evidence]:
        items = body.get("results") or body.get("data") or body.get("hits") or []
        evidence: list[Evidence] = []
        for item in items[:limit]:
            kind = _KIND_MAP.get(str(item.get("type", "paper")).lower(), SourceKind.PAPER)
            source = (
                item.get("doi")
                or item.get("id")
                or item.get("accession")
                or item.get("url")
                or "paperclip:unknown"
            )
            claim = item.get("summary") or item.get("abstract") or item.get("title") or ""
            evidence.append(
                Evidence(
                    kind=kind,
                    source=str(source),
                    claim=claim[:600],
                    quote=(item.get("snippet") or None),
                    strength=float(item.get("score", 0.6) or 0.6),
                    meta={"raw": item},
                )
            )
        return evidence
