"""Minimal stdio MCP bridge for Probception clinical evidence gathering.

The official Paperclip MCP is hosted at https://paperclip.gxl.ai/mcp. This local
bridge exists for the hackathon demo path: it exposes the exact tools Probception
needs, calls the Paperclip CLI when it is installed, and falls back to public
ClinicalTrials.gov records plus the seed comparator set when the CLI is not yet
available on the laptop.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from typing import Any

from dotenv import load_dotenv

from probception.clinical import TrialRecord, profile_to_json, score_asset, seed_trial_records
from probception.memory import get_memory_store
from probception.phase2 import (
    build_paper_fetch_plan,
    fetch_strategy_records,
    ingest_phase1_sheet,
    load_phase1_domains,
    memory_records_from_sources,
    phase1_memory_records,
)

JSON = dict[str, Any]

load_dotenv(override=False)


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = handle(request)
        except Exception as exc:  # noqa: BLE001 - MCP clients need an error response, not a crash.
            response = {
                "jsonrpc": "2.0",
                "id": _request_id(line),
                "error": {"code": -32000, "message": str(exc)},
            }
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()


def handle(request: JSON) -> JSON | None:
    method = request.get("method")
    if method == "initialize":
        return _reply(
            request,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "probception-paperclip", "version": "0.1.0"},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return _reply(request, {"tools": _tools()})
    if method == "tools/call":
        params = request.get("params", {})
        name = params.get("name")
        args = params.get("arguments") or {}
        return _reply(request, {"content": [{"type": "text", "text": call_tool(name, args)}]})
    return _error(request, -32601, f"Unsupported method: {method}")


def call_tool(name: str, args: JSON) -> str:
    if name == "paperclip_search":
        return paperclip_search(
            str(args.get("query", "")),
            source=str(args.get("source", "trials/us")),
            limit=int(args.get("limit", 10)),
        )
    if name == "gather_crispr_trial_data":
        assets = args.get("assets") or ["Casgevy", "VERVE-101", "VERVE-102", "NTLA-2001"]
        records = gather_trial_data([str(a) for a in assets])
        return json.dumps([r.model_dump(mode="json") for r in records], indent=2)
    if name == "score_clinical_asset":
        profile = score_asset(
            str(args.get("asset", "")),
            str(args.get("planned_trial_design", "")),
            trials=gather_trial_data([str(args.get("asset", ""))]),
        )
        return profile_to_json(profile)
    if name == "import_phase1_sheet_rows":
        csv_text = str(args.get("csv_text") or "")
        if csv_text:
            domains = load_phase1_domains(csv_text)
            records = phase1_memory_records(domains)
            upserts = get_memory_store().upsert_many(records)
            return json.dumps(
                {
                    "rows": len(domains),
                    "domain_keys": [domain.domain_key for domain in domains],
                    "memory_records": len(records),
                    "memory_upserts": upserts,
                },
                indent=2,
            )
        return json.dumps(ingest_phase1_sheet(), indent=2)
    if name == "memory_search_evidence":
        query = str(args.get("query", ""))
        records = get_memory_store().search(
            query,
            namespace=str(args.get("namespace", "phase2")),
            limit=int(args.get("limit", 8)),
        )
        return json.dumps([r.model_dump(mode="json") for r in records], indent=2)
    if name == "memory_upsert_evidence":
        items = args.get("items") or []
        if not isinstance(items, list):
            raise ValueError("items must be a list")
        records = memory_records_from_sources(items, namespace=str(args.get("namespace", "phase2")))
        upserts = get_memory_store().upsert_many(records)
        return json.dumps({"memory_records": len(records), "memory_upserts": upserts}, indent=2)
    if name == "collect_clinical_asset_evidence":
        asset = str(args.get("asset", ""))
        design = str(args.get("planned_trial_design", ""))
        store = get_memory_store()
        learned = store.search(f"fetch strategy {asset}", limit=3)
        plan = build_paper_fetch_plan(asset, design, learned_context=[record.text for record in learned])
        outputs = []
        for step in plan:
            outputs.append(
                {
                    "source": step["source"],
                    "query": step["query"],
                    "result": paperclip_search(step["query"], source=step["source"], limit=3),
                }
            )
        trials = gather_trial_data([asset])
        records = memory_records_from_sources(
            [trial.model_dump(mode="json") for trial in trials]
            + [{"source": "paperclip", "title": row["query"], "summary": row["result"]} for row in outputs]
            + [record.model_dump(mode="json") for record in learned]
        )
        strategy_records = fetch_strategy_records(asset, design, outputs)
        upserts = store.upsert_many(records + strategy_records)
        return json.dumps(
            {
                "asset": asset,
                "queries": plan,
                "paperclip_api": "used when PAPERCLIP_API_KEY or Paperclip CLI is configured; seed fallback otherwise",
                "learned_fetch_strategies": len(learned),
                "trial_records": len(trials),
                "memory_records": len(records) + len(strategy_records),
                "memory_upserts": upserts,
                "results": outputs,
            },
            indent=2,
        )
    if name == "memory_get_asset_context":
        asset = str(args.get("asset", ""))
        records = get_memory_store().search(asset, limit=int(args.get("limit", 8)))
        compact = [
            {
                "source_label": r.source_label,
                "kind": r.kind,
                "title": r.title,
                "text": r.text[:500],
            }
            for r in records
        ]
        return json.dumps({"asset": asset, "context": compact}, indent=2)
    raise ValueError(f"Unknown tool: {name}")


def paperclip_search(query: str, *, source: str = "trials/us", limit: int = 10) -> str:
    if not query:
        raise ValueError("query is required")
    sdk = _paperclip_search_sdk(query, source=source, limit=limit)
    if sdk is not None:
        return sdk
    exe = shutil.which("paperclip")
    if exe:
        command = [exe, "search", query, "-n", str(limit), "--source", source, "--json"]
        env = os.environ.copy()
        result = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
        return result.stderr or result.stdout or "paperclip returned no output"
    return (
        "Paperclip CLI is not installed on PATH. Configure the hosted MCP at "
        "https://paperclip.gxl.ai/mcp or install the CLI; using seed records for scoring."
    )


def _paperclip_search_sdk(query: str, *, source: str, limit: int) -> str | None:
    key = os.environ.get("PAPERCLIP_API_KEY", "").strip()
    if not key:
        return None
    try:
        from gxl_paperclip import APIKeyAuth, PaperclipClient  # type: ignore[import-not-found]

        client = PaperclipClient(auth=APIKeyAuth(key))
        result = client.search(query, limit=limit, source=source)
        if hasattr(result, "model_dump_json"):
            return result.model_dump_json(indent=2)
        return json.dumps({"output": getattr(result, "output", str(result))}, indent=2)
    except Exception:
        return None


def gather_trial_data(assets: list[str]) -> list[TrialRecord]:
    seed = seed_trial_records()
    records: list[TrialRecord] = []
    for asset in assets:
        matches = [t for t in seed if _matches(asset, t)]
        if matches:
            records.extend(matches)
            continue
        if asset.upper().startswith("NCT"):
            records.append(_fetch_ctgov(asset))
    return records or seed


def _fetch_ctgov(nct_id: str) -> TrialRecord:
    with urllib.request.urlopen(
        f"https://clinicaltrials.gov/api/v2/studies/{nct_id}", timeout=20
    ) as response:
        body = json.loads(response.read().decode("utf-8"))
    protocol = body["protocolSection"]
    identification = protocol.get("identificationModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {})
    design = protocol.get("designModule", {})
    status = protocol.get("statusModule", {})
    return TrialRecord(
        asset=nct_id,
        nct_id=nct_id,
        name=identification.get("briefTitle", ""),
        sponsor=sponsor.get("name", ""),
        phase=",".join(design.get("phases") or []),
        start_date=(status.get("startDateStruct") or {}).get("date", ""),
        completion_date=(status.get("completionDateStruct") or {}).get("date", ""),
        status=status.get("overallStatus", ""),
        enrollment=(design.get("enrollmentInfo") or {}).get("count"),
        source="clinicaltrials.gov",
    )


def _matches(asset: str, trial: TrialRecord) -> bool:
    text = asset.lower()
    candidates = {trial.asset.lower(), trial.nct_id.lower(), trial.guide_or_target.lower()}
    candidates.update(part for part in trial.asset.lower().replace("/", " ").split() if len(part) > 3)
    return any(candidate and candidate in text for candidate in candidates)


def _tools() -> list[JSON]:
    return [
        {
            "name": "paperclip_search",
            "description": "Search Paperclip sources such as ClinicalTrials.gov, FDA, PMC, bioRxiv, UniProt, PDB, and ChEMBL.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "source": {"type": "string", "default": "trials/us"},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["query"],
            },
        },
        {
            "name": "gather_crispr_trial_data",
            "description": "Return normalized trial facts for Casgevy, VERVE-101, VERVE-102, NTLA-2001, or NCT ids.",
            "inputSchema": {
                "type": "object",
                "properties": {"assets": {"type": "array", "items": {"type": "string"}}},
            },
        },
        {
            "name": "score_clinical_asset",
            "description": "Generate the Probception deterministic clinical risk profile for an in vivo CRISPR asset.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "asset": {"type": "string"},
                    "planned_trial_design": {"type": "string"},
                },
                "required": ["asset", "planned_trial_design"],
            },
        },
        {
            "name": "import_phase1_sheet_rows",
            "description": "Fetch or import Phase 1 Google Sheet rubric rows and write compact domain records to memory.",
            "inputSchema": {
                "type": "object",
                "properties": {"csv_text": {"type": "string"}},
            },
        },
        {
            "name": "collect_clinical_asset_evidence",
            "description": "Fan out Paperclip searches and trial gathering for a clinical asset, then store reusable memory records.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "asset": {"type": "string"},
                    "planned_trial_design": {"type": "string"},
                },
                "required": ["asset", "planned_trial_design"],
            },
        },
        {
            "name": "memory_search_evidence",
            "description": "Search Atlas memory first, falling back to local deterministic JSONL memory.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "namespace": {"type": "string", "default": "phase2"},
                    "limit": {"type": "integer", "default": 8},
                },
                "required": ["query"],
            },
        },
        {
            "name": "memory_upsert_evidence",
            "description": "Store normalized source/evidence records in Atlas or local fallback memory.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "default": "phase2"},
                    "items": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["items"],
            },
        },
        {
            "name": "memory_get_asset_context",
            "description": "Return compact source-label context for a clinical asset to reduce prompt tokens.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "asset": {"type": "string"},
                    "limit": {"type": "integer", "default": 8},
                },
                "required": ["asset"],
            },
        },
    ]


def _reply(request: JSON, result: JSON) -> JSON:
    return {"jsonrpc": "2.0", "id": request.get("id"), "result": result}


def _error(request: JSON, code: int, message: str) -> JSON:
    return {"jsonrpc": "2.0", "id": request.get("id"), "error": {"code": code, "message": message}}


def _request_id(raw: str) -> Any:
    try:
        return json.loads(raw).get("id")
    except json.JSONDecodeError:
        return None


if __name__ == "__main__":
    main()
