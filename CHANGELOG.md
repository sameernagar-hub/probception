# Changelog

All notable changes to Probception. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Design *decisions* and their rationale live in
[docs/EXECUTION_LOG.md](docs/EXECUTION_LOG.md) — this file records what shipped.

---

## [Unreleased]

### Added
- Clinical asset derisking workflow for in vivo CRISPR: `probception risk-profile`
  accepts an asset plus planned trial design and writes a structured JSON profile
  plus standalone responsive HTML report.
- Deterministic safety and efficacy scoring across cell, animal, and human
  evidence domains, with confidence, FDA approval proxy, commercial-success
  proxy, inverse-score bottleneck weighting, and explicit reasoning.
- Seed comparator data for Casgevy / exa-cel, VERVE-101, VERVE-102, and
  NTLA-2001.
- Local Paperclip MCP bridge at `scripts/paperclip_mcp.py`, exposing
  `paperclip_search`, `gather_crispr_trial_data`, and `score_clinical_asset`.
- Phase 2 sheet ingestion with `probception ingest-phase1`, including normalized
  CSV/JSON outputs for the 12 FDA review-domain rows.
- Atlas-backed agent memory with deterministic JSONL fallback and hash-based
  embeddings for local retrieval when Atlas/vector search is unavailable.
- Additional Paperclip MCP tools for Phase 1 sheet import, clinical asset
  evidence gathering, memory upserts, memory search, and compact asset context.
- Tamarind hosted-job adapter with deterministic outcome containment.
- `.mcp.example.json` with both the hosted Paperclip MCP and the local
  Probception bridge.
- Resilient live adapter wrappers. Paperclip/Proto failures degrade to
  deterministic mock evidence or observations while preserving failure reasons
  in metadata.

### Changed
- Paperclip adapter now tries the official Python SDK, then the CLI, then direct
  HTTP with `X-API-Key`.
- README, setup, integration, clinical workflow, and execution-log docs now
  describe the finalized clinical derisking direction, Phase 2 memory loop, and
  fallback behavior.
- Removed `docs/COORDINATION.md`; Phase 2 coordination now lives in source
  labels, memory records, and the execution log.

### To come
- Science-team manual review of the seed clinical asset data
- Claude skill generation and validation for Phase 2
- Retrodiction benchmark: predict a known result the agent was never shown

---

## [0.1.0] — 2026-08-15

First working version. Complete closed loop, verified end to end.

### Added

**Reasoning core**
- `BeliefState` — a first-class probability distribution over hypotheses, with
  Bayes update, Shannon entropy, outcome prediction, and surprise in bits
- Expected-information-gain planner (`design/eig.py`) ranking candidate
  experiments by information per unit cost
- Novelty discount so repeated runs of the same protocol are valued at
  `0.45^n` of face value — EIG assumes conditional independence, which is false
  for repeats of one assay
- `Scientist` interface with two implementations: `LLMScientist` (Claude Opus 5)
  and `HeuristicScientist` (deterministic, no API key, doubles as an ablation arm)

**Provenance**
- Append-only, hash-chained JSONL ledger; each entry's id hashes its own content
  and its predecessor, so post-hoc edits are detectable
- `probception verify` re-walks the chain — with a test proving a tamper is caught
- Content-addressed `Evidence` ids, so a citation cannot drift from its source
- Standalone HTML inspector with zero external assets: every candidate
  considered, its EIG/cost/utility, the prediction made before the result, the
  observation, the surprise, and the before/after posterior

**Validation**
- Counterfactual replay harness: the same agent across contradictory worlds,
  diffing what it proposes next. `probception counterfactual` exits non-zero if
  the loop is open
- Calibration scoring (Brier, log score, top-1 accuracy) computed from the
  ledger alone against an explicit uninformed baseline

**Integrations**
- `SearchAdapter` / `ExperimentAdapter` interfaces — the only places the system
  touches the outside world
- Paperclip adapter (evidence) and Proto adapter (design-as-experiment, with
  outcome thresholds ledgered before submission)
- Mock and scripted adapters so the entire loop runs with zero credentials
- Claude wrapper with structured outputs, prompt caching on the stable system
  prefix, configurable effort, and full call tracing to the ledger

**Interface**
- CLI: `doctor` · `demo` · `ask` · `counterfactual` · `score` · `report` ·
  `verify` · `runs`

**Project**
- 31 tests covering belief math, EIG, ledger integrity, and the end-to-end loop
- Ruff clean; GitHub Actions CI on Linux, macOS and Windows
- `.gitattributes` pinning LF, because ledger ids are content hashes and
  CRLF drift across a mixed-OS team would break reproducibility
- Documentation: setup, coordination, architecture, integrations, execution log,
  credits

### Fixed during initial build
- Planner degenerated into repeating the single cheapest assay at every step;
  fixed by the novelty discount described above (found by running the demo, not
  by reading the code)
- `Hypothesis.prior` correctly rejects values outside [0,1]; `BeliefState`
  normalises priors that are individually valid but don't sum to 1 — the common
  case when a language model assigns them independently

### Known limitations
Documented in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#known-limitations).
The one that matters most: likelihood tables are elicited from the LLM, so a
confidently wrong table yields a confidently wrong posterior. The Bayesian
framing does not by itself make the model's numbers trustworthy, and we would
rather say so than imply otherwise.

[Unreleased]: https://github.com/sameernagar-hub/probception/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sameernagar-hub/probception/releases/tag/v0.1.0
