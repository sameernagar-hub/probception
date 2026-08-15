# Clinical Asset Derisking Workflow

This is the finalized pre-phase hackathon product direction.

## Input

A clinical asset plus planned trial design.

Example:

```bash
uv run probception risk-profile "VERVE-102 PCSK9 GalNAc-LNP" \
  "Phase 1b/2 single ascending dose in HeFH or premature CAD; endpoints: safety, PCSK9, LDL-C"
```

## Output

The command writes:

- `risk_profile.json` — structured scores for downstream product work
- `risk_report.html` — standalone, responsive, no-server report for judging

Scores cover:

- safety and efficacy in cell, animal, and human evidence domains
- confidence
- final success score
- FDA approval proxy
- commercial success proxy

Weak scores are upweighted with an inverse-score term so the profile is driven
by bottlenecks instead of a flattering average.

## Evidence Sources

Primary live source is Paperclip because it indexes PMC, arXiv, bioRxiv,
medRxiv, OpenAlex abstracts, FDA, ClinicalTrials.gov, international registries,
UniProt, PDB, and ChEMBL from one agent-native interface.

Current seed comparators:

| Asset | Trial | Sponsor | Phase | Why it matters |
|---|---|---|---|---|
| Casgevy / exa-cel / CTX001 | NCT03745287 | Vertex | Phase 2/3 | FDA-approved CRISPR precedent, but ex vivo and not LNP |
| VERVE-101 | NCT05398029 | Verve | Phase 1 | Direct in vivo LNP PCSK9 base-editing precedent |
| VERVE-102 | NCT06164730 | Verve | Phase 1 | Best public analogue for GalNAc-LNP PCSK9 editing |
| NTLA-2001 | NCT04601051 | Intellia | Phase 1 | Key in vivo CRISPR-Cas9 LNP human precedent |

## Paperclip MCP

Use the official hosted MCP when the client supports remote MCP:

```text
https://paperclip.gxl.ai/mcp
Authorization: Bearer ${PAPERCLIP_API_KEY}
```

This repo also includes a local stdio bridge:

```bash
uv run python scripts/paperclip_mcp.py
```

See `.mcp.example.json` for both configurations. The local bridge exposes:

- `paperclip_search`
- `gather_crispr_trial_data`
- `score_clinical_asset`

## Deterministic Fallbacks

The clinical workflow must render even when every live account fails.

Fallback order:

| Surface | Primary | Fallback |
|---|---|---|
| Evidence gathering | Paperclip SDK, CLI, hosted MCP, or direct HTTP | seed comparator records plus deterministic mock evidence |
| Clinical trial records | Paperclip/ClinicalTrials.gov | built-in Casgevy, VERVE-101, VERVE-102, NTLA-2001 records |
| Experiment execution | Proto/Modal/Tamarind adapter | deterministic mock lab with declared outcome labels |
| Reasoning | Claude | `HeuristicScientist` deterministic reasoner |

Fallbacks are not hidden. The failure reason is preserved in evidence metadata
or `observation.raw`, so the report remains inspectable.

## Phase Plan

Phase 1, science team:

- manually review clinical asset data
- mark which evidence is cell, animal, or human
- identify nonstarters and known failure modes
- validate whether the hardcoded score rubric is defensible

Phase 2, engineering/product:

- review the science labels and score outputs
- generate the full agent flow
- turn the workflow into a Claude skill
- validate the Claude skill against held-out successful and failed clinical trials

## Guardrail

The LLM may explain or propose evidence to inspect. It must not set final scores,
rank experiments, or update beliefs. Scores remain deterministic and auditable.
