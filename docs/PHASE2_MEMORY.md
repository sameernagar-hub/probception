# Phase 2 Memory And MCP

Phase 2 turns the Phase 1 review rubric into reusable agent memory.

## What Changed

- `probception ingest-phase1` fetches the public Google Sheet via the `gviz`
  CSV endpoint and writes normalized CSV/JSON seed files.
- `memory.py` provides Atlas-first memory with deterministic local JSONL
  fallback.
- `scripts/paperclip_mcp.py` now exposes Phase 2 tools:
  - `import_phase1_sheet_rows`
  - `collect_clinical_asset_evidence`
  - `memory_search_evidence`
  - `memory_upsert_evidence`
  - `memory_get_asset_context`
- `collect_clinical_asset_evidence` fetches fresh evidence on demand across
  trials, FDA, PMC, arXiv, bioRxiv, medRxiv, and OpenAlex-style source routes.
  Each attempt is stored as a `fetch_strategy` memory record so later agents can
  reuse the route instead of rediscovering it. When `PAPERCLIP_API_KEY` is set,
  each route calls the Paperclip SDK/API path; otherwise the bridge tries the
  Paperclip CLI and then records deterministic fallback metadata.

## Refinement Loop

1. Search memory for previous `fetch_strategy` records for the asset.
2. Extract stable refinement hints such as off-target, biodistribution,
   immunogenicity, dose-response, LDL-C, PCSK9, liver, and LNP.
3. Build source-specific Paperclip queries with those hints.
4. Store the new evidence snippets and the fetch strategy that found them.

This makes future fetches adapt to what worked while keeping scoring and belief
updates outside memory.

## Collections

Default Atlas database and collection:

- database: `probception`
- collection: `agent_memory`

Each memory record has:

- `namespace`
- `kind`
- `source`
- `source_label`
- `title`
- `text`
- `metadata`
- `embedding`

The fallback embedding is deterministic hashing. Atlas Vector Search can replace
the index with a real embedding later without changing the MCP surface.

## Guardrail

Memory is retrieval and caching only. It does not set scores, rank experiments,
or update beliefs.
