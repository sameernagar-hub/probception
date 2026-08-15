"""Provenance guarantees. A tamper that goes undetected here is a demo that fails."""

from __future__ import annotations

from probception.trace.ledger import Ledger
from probception.types import Evidence, SourceKind


def test_append_and_read_roundtrip(tmp_path):
    ledger = Ledger("t1", tmp_path)
    ledger.append("thing_happened", {"a": 1})
    ledger.append("thing_happened", {"a": 2})
    entries = ledger.read()
    assert len(entries) == 2
    assert entries[0]["payload"]["a"] == 1
    assert entries[1]["seq"] == 1


def test_chain_verifies_when_untouched(tmp_path):
    ledger = Ledger("t2", tmp_path)
    for i in range(5):
        ledger.append("step", {"i": i})
    ok, message = ledger.verify()
    assert ok, message


def test_verify_detects_an_edited_entry(tmp_path):
    ledger = Ledger("t3", tmp_path)
    ledger.append("step", {"value": "original"})
    ledger.append("step", {"value": "second"})

    # Tamper: rewrite the first line's payload but leave its id in place.
    lines = ledger.path.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0].replace("original", "forged")
    ledger.path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    ok, message = Ledger.load("t3", tmp_path).verify()
    assert not ok
    assert "modified" in message or "chain broken" in message


def test_pydantic_payloads_serialise(tmp_path):
    ledger = Ledger("t4", tmp_path)
    ev = Evidence(kind=SourceKind.PAPER, source="10.1000/x", claim="something is true")
    ledger.append("evidence_gathered", [ev])
    payload = ledger.read()[0]["payload"]
    assert payload[0]["claim"] == "something is true"
    assert payload[0]["id"].startswith("ev_")


def test_resume_continues_the_chain(tmp_path):
    first = Ledger("t5", tmp_path)
    first.append("a", {})
    first.append("b", {})

    resumed = Ledger("t5", tmp_path)
    resumed.append("c", {})

    entries = resumed.read()
    assert [e["event"] for e in entries] == ["a", "b", "c"]
    assert entries[2]["seq"] == 2
    ok, _ = resumed.verify()
    assert ok


def test_evidence_id_is_content_addressed():
    a = Evidence(kind=SourceKind.PAPER, source="s", claim="c")
    b = Evidence(kind=SourceKind.PAPER, source="s", claim="c")
    c = Evidence(kind=SourceKind.PAPER, source="s", claim="different")
    assert a.id == b.id
    assert a.id != c.id
