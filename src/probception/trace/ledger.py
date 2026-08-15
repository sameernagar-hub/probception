"""The provenance ledger: an append-only record of everything the agent did.

Design rule: nothing in Probception changes belief without writing a ledger
entry first. If it is not in the ledger, it did not happen. That single rule is
what lets us answer "why did the agent decide that?" months later, from disk,
with no live model in the loop.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from probception.types import content_id


class Ledger:
    """Append-only JSONL, one event per line, each hash-chained to the last.

    The chain means an entry cannot be quietly edited after the fact: change any
    earlier line and every later `prev` hash stops matching.
    """

    def __init__(self, run_id: str, root: Path | str = "runs"):
        self.run_id = run_id
        self.dir = Path(root) / run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "ledger.jsonl"
        self._prev = "genesis"
        self._n = 0
        if self.path.exists():
            self._resume()

    def _resume(self) -> None:
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                self._n += 1
                self._prev = json.loads(line)["id"]

    def append(self, event: str, payload: Any, note: str = "") -> dict[str, Any]:
        """Record one event. Returns the written entry."""
        if isinstance(payload, BaseModel):
            body = payload.model_dump(mode="json")
        elif isinstance(payload, list):
            body = [p.model_dump(mode="json") if isinstance(p, BaseModel) else p for p in payload]
        else:
            body = payload

        entry = {
            "seq": self._n,
            "event": event,
            "at": datetime.now(UTC).isoformat(),
            "note": note,
            "prev": self._prev,
            "payload": body,
        }
        entry["id"] = content_id(entry, "ent")
        # newline="\n" keeps the ledger byte-identical across Windows and POSIX,
        # which matters because entry ids are hashes of the file's content.
        with self.path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")
        self._prev = entry["id"]
        self._n += 1
        return entry

    # -- reading back ----------------------------------------------------
    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(ln) for ln in self.path.read_text(encoding="utf-8").splitlines() if ln.strip()]

    def events(self, kind: str) -> list[dict[str, Any]]:
        return [e for e in self.read() if e["event"] == kind]

    def verify(self) -> tuple[bool, str]:
        """Re-walk the hash chain. This is the integrity check we demo."""
        prev = "genesis"
        for i, entry in enumerate(self.read()):
            if entry["prev"] != prev:
                return False, f"chain broken at seq {i}: expected prev={prev}"
            recomputed = content_id({k: v for k, v in entry.items() if k != "id"}, "ent")
            if recomputed != entry["id"]:
                return False, f"entry {i} was modified after it was written"
            prev = entry["id"]
        return True, f"{self._n} entries verified, chain intact"

    @staticmethod
    def load(run_id: str, root: Path | str = "runs") -> Ledger:
        return Ledger(run_id, root)
