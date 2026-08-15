# Integrations

Every external tool, what we use it for, how to get credentials, and how it
plugs into the loop.

**The integration philosophy:** every tool enters through one of two verbs —
`search()` returning `Evidence`, or `run()` returning an `Observation`. Nothing
else in the codebase knows a vendor's name. That is why we can swap Proto for
Tamarind, or Paperclip for a local corpus, without touching the reasoning layer.

---

## Credential redemption — do this first

Claim these at check-in. Several are capped and run out.

| Tool | What you get | How to claim |
|---|---|---|
| **Anthropic** | $50 API credits, 90-day validity | Account at [platform.claude.com](https://platform.claude.com), then redeem at [the re:AGENT offer link](https://platform.claude.com/offers/06628132-91eb-4a12-abe4-47c70481280d) |
| **GXL Paperclip** | Higher rate limits | Account at [paperclip.gxl.ai/login](https://paperclip.gxl.ai/login), then [redeem `HACKATHON2026`](https://paperclip.gxl.ai/redeem?code=HACKATHON2026) |
| **Modal** | $100 compute | [modal.fillout.com/t/qMXCmRGseUus](https://modal.fillout.com/t/qMXCmRGseUus) → `pip install modal` → `modal setup` |
| **Proto** | Design framework access | Proto installation & credits slide |
| **Tamarind** | 100 hosted jobs | Log in, then [app.tamarind.bio/code/gxl-hackathon-26](https://app.tamarind.bio/code/gxl-hackathon-26) |
| **Benchling** | AI credits + MCP server + API | [hackathon.bnchdev.org](https://hackathon.bnchdev.org) with your provisioned account |
| **Phylo / Biomni** | Pro plan, daily limit lifted | [biomni.phylo.bio](https://biomni.phylo.bio) with an institutional email → avatar → Settings → Usage & Billing → coupon `RE-AGENT-2026` |

> ⚠️ **Anthropic credits are capped at 200 claims across the whole event.** Claim
> yours in the first hour. If `.edu`/personal email verification blocks you, ask
> the organisers — they can approve manually.
>
> ⚠️ **Phylo requires an institutional email** and your *Personal* workspace must
> be selected before applying the coupon.

Put everything in `.env` (copy from `.env.example`). **`.env` is gitignored.
Never commit a key.**

---

## Anthropic — Claude Opus 5

**What it does for us:** generates falsifiable hypotheses with priors, and designs
candidate experiments with full likelihood tables. That is the creative,
open-ended work — exactly what a frontier model is good at.

**What it deliberately does *not* do:** score experiments or update beliefs.
Those are deterministic arithmetic in `design/eig.py` and `belief/state.py`. If
the LLM could nudge the posterior, no run would be reproducible and no decision
would be auditable.

**How we use the API** (`agents/llm.py`):

| Feature | Why |
|---|---|
| **Structured outputs** (`messages.parse` with a Pydantic schema) | Hypotheses and experiments come back as validated objects, not prose we have to regex. A malformed likelihood table fails at the boundary, not three layers deeper. |
| **Prompt caching** on the system prefix | The falsifiability contract is identical on every call in a run. Caching it means repeated steps read the prefix at ~0.1× input cost — meaningful when the loop runs dozens of times. |
| **Adaptive thinking + `effort`** | On by default for Opus 5. `effort=high` for real reasoning; drop to `medium` if the credit budget gets tight. |
| **Full call tracing** | Every call writes model, effort, latency, token usage and cache hits to the ledger. You can see exactly what a conclusion cost. |

```python
# The prompt-caching arrangement that matters:
system_blocks = [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}]
# Stable contract above the breakpoint. Volatile per-step content in the user
# turn, below it, where it cannot invalidate the cache.
```

**Config:** `ANTHROPIC_API_KEY`, `PROBCEPTION_MODEL` (default `claude-opus-5`),
`PROBCEPTION_EFFORT` (default `high`).

**Cost control:** the deterministic reasoner (`--offline`) costs nothing and runs
the identical loop. Use it while developing; save credits for the demo.

---

## GXL Paperclip — the evidence layer

**What it does for us:** turns papers, datasets, clinical trials and biological
databases into retrievable evidence.

**The creative bit:** we don't use Paperclip as a search box that dumps abstracts
into a prompt. Every hit becomes a content-addressed `Evidence` object with an
explicit `strength`, and those strengths are what shape the **priors** the agent
starts from. Retrieval feeds inference numerically rather than as vibes-in-context.

**Implementation:** `adapters/paperclip.py`

The adapter tries supported surfaces in order:

1. `gxl_paperclip` Python SDK, if installed
2. `paperclip` CLI, if present on `PATH`
3. direct HTTP fallback with `X-API-Key`

If all of those fail in live mode, `ResilientSearchAdapter` falls back to the
deterministic mock evidence corpus and preserves the failure reason in evidence
metadata. A broken Paperclip connection should never take down the full demo.

```python
Evidence(
    kind=SourceKind.PAPER,
    source="10.1038/s41586-021-03819-2",   # the citation IS the id
    claim="Structure prediction degrades below 30 homologs.",
    strength=0.8,                           # feeds the prior
)
```

Evidence ids are hashes of their own content, so a citation cannot drift from the
thing it cites.

**Config:** `PAPERCLIP_API_KEY`, `PAPERCLIP_BASE_URL`

**MCP:** hosted remote MCP is `https://paperclip.gxl.ai/mcp` with header
`X-API-Key: ${PAPERCLIP_API_KEY}`. The repo also ships a local stdio bridge at
`scripts/paperclip_mcp.py` exposing `paperclip_search`,
`gather_crispr_trial_data`, and `score_clinical_asset`.

**If the endpoint shape differs from our guess:** fix `_ENDPOINT` and `_parse` in
`adapters/paperclip.py`. Nothing downstream changes — that's the point of the
adapter boundary.

---

## Proto — biological design as an experiment

**What it does for us:** designs DNA / RNA / protein sequences against custom
criteria.

**The creative bit, and it's the one we'd defend to a judge:** we do not treat a
design run as "generate some candidates." We treat it as **an experiment with
pre-declared discrete outcomes** (`hit` / `weak` / `miss`) whose likelihoods under
each hypothesis are written to the ledger **before the job is submitted**.

That means the thresholds separating a hit from a miss are fixed in advance and
hash-chained. You cannot look at the score distribution and then decide what
counts as success. A design campaign becomes something you can be *wrong* about.

**Implementation:** `adapters/proto.py`

```python
Experiment(
    title="Design binders against target X",
    outcomes=[Outcome(label="hit"), Outcome(label="weak"), Outcome(label="miss")],
    likelihoods={...},                                  # declared up front
    params={"hit_threshold": 0.8, "weak_threshold": 0.5},  # ledgered before submit
    tool="proto",
)
```

**Config:** `PROTO_API_KEY`, `PROTO_BASE_URL`

If Proto is configured but the request fails, `ResilientExperimentAdapter`
falls back to the deterministic mock lab and stores the failure reason in
`observation.raw`. The Bayes update still only sees a declared outcome label.

---

## Modal — the compute substrate

**What it does for us:** runs anything that needs a GPU or more than a laptop —
ESM embedding sweeps, Boltz structure prediction, Proto's heavier tools.

**How it fits:** Modal is invoked *inside* an experiment adapter, never from the
reasoning layer. The loop only ever sees "an experiment ran and returned an
outcome label" — it neither knows nor cares that a GPU was involved.

```bash
uv sync --extra compute
uv run modal setup
```

**Config:** `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`

**Budget note:** $100 goes fast on GPU time. Prefer batching one sweep over many
interactive calls, and launch long jobs at the Saturday-night checkpoint.

---

## ESM / Boltz — representations and structure

**What they do for us:** protein language model embeddings and structure
prediction — the substrate for hypotheses about sequence–function relationships.

**How they fit:** as experiment adapters running on Modal. An ESM sweep is an
experiment whose outcome is discretised against a pre-declared threshold, exactly
like a Proto design run.

**A hypothesis this makes testable:** *"embedding distance predicts stability
effect well enough to replace a wet-lab pre-screen."* That is falsifiable, it has
a natural held-out set (ProteinGym DMS assays), and the agent can design
experiments that discriminate it from "the correlation is real but too weak to
act on."

---

## Tamarind — hosted jobs

**What it does for us:** 100 pre-configured bioinformatics jobs with no
infrastructure work. The fastest path from "we should try X" to a result.

**How it fits:** an experiment adapter. Best use is as an **orthogonal readout** —
a second method that shares no failure mode with the first. Our EIG planner values
these highly *because* they are independent, which is a nice case where the
information-theoretic scoring and the scientific instinct agree.

**Config:** `TAMARIND_API_KEY`

---

## Benchling — LIMS + MCP

**What it does for us:** the bridge to real wet-lab reality. The MCP server is
included in the hackathon credits, which makes it directly agent-accessible.

**How it fits:** two ways.
1. **Evidence source** — prior experimental results from the LIMS become
   `Evidence` that shapes priors.
2. **Experiment sink** — the agent's proposed next experiment gets written back
   as a real protocol a human could actually run on Monday.

That second one closes the loop *out of the computer*, which is the most
compelling version of "closing the loop" available to us.

**Config:** `BENCHLING_API_KEY`, `BENCHLING_TENANT`

---

## Phylo / Biomni

**What it does for us:** a biomedical agent platform, useful as a **comparison
baseline** — run the same question through Phylo and through Probception and
compare not just the answers but the *auditability* of the answers.

**Config:** `PHYLO_API_KEY`

---

## How to add a new tool

The whole point of the adapter boundary is that this is small.

**1. Write the adapter** (`src/probception/adapters/yourtool.py`):

```python
from probception.adapters.base import ExperimentAdapter
from probception.types import Experiment, Observation

class YourToolAdapter(ExperimentAdapter):
    name = "yourtool"

    def available(self) -> bool:
        return bool(self.api_key)

    def run(self, experiment: Experiment) -> Observation:
        result = ...  # call the thing
        return Observation(
            experiment_id=experiment.id,
            outcome_label=self._classify(result, experiment),  # must be a declared outcome
            raw=result,          # keep everything — the ledger stores it
            source=self.name,
            held_out=True,
        )
```

**2. Register it** in `adapters/__init__.py` under `get_lab()`.

**3. Add credentials** to `.env.example` and `config.py`.

**Two rules that are not negotiable:**

- `outcome_label` **must** be one of the labels declared on the experiment. The
  Bayes update indexes the likelihood table by that string; inventing a new label
  silently corrupts the posterior.
- Any threshold that turns a continuous score into a discrete outcome goes in
  `experiment.params`, so it is ledgered **before** the job runs.

---

## Failure modes we planned for

| Failure | What happens | Why we're fine |
|---|---|---|
| Conference wifi dies | Live adapters fail | Mock adapters run the whole loop offline; HTML inspector needs no network |
| A partner API changes shape | One adapter breaks | Reasoning layer untouched; fix `_parse` and move on |
| Anthropic credits exhausted | No LLM hypotheses | `--offline` deterministic reasoner runs the identical loop |
| Modal budget gone | No GPU experiments | Scripted adapter still demonstrates the closed loop |
| A tool returns something unexpected | Adapter raises | `raw` is preserved in the ledger for debugging |
| A live adapter raises during a demo | Resilient wrapper catches it | Deterministic fallback returns evidence or an observation with the failure reason in metadata |

Every one of these degrades to a working demo. That was a design requirement,
not an accident.
