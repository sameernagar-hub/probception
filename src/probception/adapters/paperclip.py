"""GXL Paperclip adapter — papers, datasets, clinical trials, biological databases.

Paperclip is our evidence layer. Its job in Probception is not "find me papers"
but "find me things that would move a prior", so every hit is converted into an
`Evidence` object with an explicit strength, and the raw response is retained in
`meta` so a reviewer can go back to the source.

The endpoint shape below is best-effort against the hackathon API. If it drifts,
fix `_ENDPOINT` and `_parse` — everything downstream is insulated from the change.
"""

from __future__ import annotations

import json
import shutil
import subprocess
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
        sdk_results = self._search_sdk(query, limit)
        if sdk_results is not None:
            return sdk_results
        cli_results = self._search_cli(query, limit)
        if cli_results is not None:
            return cli_results
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}{_ENDPOINT}",
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                },
                json={"query": query, "limit": limit},
            )
            response.raise_for_status()
            return self._parse(response.json(), limit)

    def _search_sdk(self, query: str, limit: int) -> list[Evidence] | None:
        try:
            from gxl_paperclip import APIKeyAuth, PaperclipClient  # type: ignore[import-not-found]
        except ImportError:
            return None
        try:
            client = PaperclipClient(auth=APIKeyAuth(self.api_key))
            result = client.search(query, limit=limit, source="trials,pmc,biorxiv,medrxiv,fda")
        except Exception:
            return None
        output = getattr(result, "output", "")
        raw = getattr(result, "model_dump", lambda: {"output": output})()
        return [
            Evidence(
                kind=SourceKind.CLINICAL_TRIAL if "trial" in query.lower() else SourceKind.PAPER,
                source=getattr(result, "result_id", "paperclip:sdk"),
                claim=str(output)[:600],
                strength=0.7,
                meta={"raw": raw},
            )
        ]

    def _search_cli(self, query: str, limit: int) -> list[Evidence] | None:
        exe = shutil.which("paperclip")
        if not exe:
            return None
        try:
            result = subprocess.run(
                [
                    exe,
                    "search",
                    query,
                    "-n",
                    str(limit),
                    "--source",
                    "trials,pmc,biorxiv,medrxiv,fda",
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=self.timeout,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if result.returncode != 0 or not result.stdout.strip():
            return None
        try:
            body: Any = json.loads(result.stdout)
        except json.JSONDecodeError:
            body = {"results": [{"source": "paperclip:cli", "summary": result.stdout}]}
        return self._parse(body, limit)

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
