"""Phase 2 sheet ingestion and memory fallbacks."""

from __future__ import annotations

import json
import subprocess
import sys

from probception.memory import LocalMemoryStore, MemoryRecord, canonical_source_label
from probception.phase2 import (
    DOMAIN_KEYS,
    build_paper_fetch_plan,
    fetch_strategy_records,
    load_phase1_domains,
    phase1_memory_records,
)

SHEET_CSV = '''"FDA Review Domain","Core Regulatory Question","Primary Review Data (Act 1)","Detailed Review Elements & Dossier Components"
"Disease Context","What is the disease?","Natural history","Severity"
"Trial design
","Is the trial adequate?","Protocol","Endpoints"
'''


def test_phase1_rows_get_stable_domain_keys():
    domains = load_phase1_domains(SHEET_CSV)
    assert [d.domain_key for d in domains] == DOMAIN_KEYS[:2]
    assert domains[1].review_domain == "Trial design"


def test_phase1_rows_become_memory_records():
    records = phase1_memory_records(load_phase1_domains(SHEET_CSV))
    assert records[0].source_label == "phase1:disease_context_mechanism"
    assert records[0].embedding


def test_local_memory_search_round_trip(tmp_path):
    store = LocalMemoryStore(tmp_path / "memory.jsonl")
    store.upsert_many(
        [
            MemoryRecord(
                kind="source_document",
                source="NCT03745287",
                source_label="ctgov:NCT03745287",
                title="Casgevy trial",
                text="BCL11A sickle cell trial safety and efficacy",
            )
        ]
    )
    hits = store.search("BCL11A safety", limit=1)
    assert hits[0].source_label == "ctgov:NCT03745287"


def test_canonical_source_labels_are_compact():
    assert canonical_source_label("https://clinicaltrials.gov/study/NCT03745287") == "ctgov:NCT03745287"
    assert canonical_source_label("https://paperclip.gxl.ai/citations/fda/fda_abc123#L1") == "fda:fda_abc123"


def test_paper_fetch_plan_and_strategy_memory_are_deterministic():
    plan = build_paper_fetch_plan("VERVE-102", "Phase 1b/2")
    assert {step["source"] for step in plan} >= {"trials/us", "pmc", "biorxiv", "medrxiv"}
    refined = build_paper_fetch_plan("VERVE-102", "Phase 1b/2", learned_context=["Query: PCSK9 liver LDL-C"])
    assert "pcsk9" in refined[0]["query"].lower()
    assert "liver" in refined[0]["query"].lower()
    records = fetch_strategy_records("VERVE-102", "Phase 1b/2", plan[:2])
    assert records[0].kind == "fetch_strategy"
    assert records[0].source_label.startswith("fetch:verve_102:")


def test_mcp_lists_phase2_memory_tools():
    message = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    result = subprocess.run(
        [sys.executable, "scripts/paperclip_mcp.py"],
        input=json.dumps(message) + "\n",
        capture_output=True,
        text=True,
        check=True,
    )
    names = {tool["name"] for tool in json.loads(result.stdout)["result"]["tools"]}
    assert {"import_phase1_sheet_rows", "memory_search_evidence", "collect_clinical_asset_evidence"} <= names
