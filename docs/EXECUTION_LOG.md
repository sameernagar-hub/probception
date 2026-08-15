# Execution log

A running record of what we did, what we decided, and what we learned — kept
during the event, not reconstructed after it.

**Format:** newest entry at the top. Every entry gets a timestamp, an author, and
where relevant, the decision made and its rationale. Decisions get a `DEC-n` id
so they can be referenced from PRs and from the demo.

> **Why keep this.** Two reasons. Judges ask "how did you get here?" and a real
> log beats a reconstructed story. And at 2am on Sunday, this is how you remember
> why you rejected the approach you're about to re-propose.

---

## Day 1 — Saturday, 15 August 2026

### 13:45 · Teammate evidence map fetched and linked · Codex

Fetched new `origin/main` commit `04f98cf`, which added
`REGULATORY_EVIDENCE_MAP.md`. It is additive and does not conflict with the
clinical derisking branch. The branch was rebased on top of it, and the README
plus clinical workflow docs now link to the FDA evidence map.

---

### 13:35 · Windows CI console encoding fixed · Codex

GitHub Actions passed on Linux and macOS, but Windows failed during
`probception demo --steps 2` because Rich tried to print Unicode block bars to a
legacy `cp1252` console. Terminal-facing CLI output is now ASCII-safe.

**Verified:**
```
uv run probception demo --steps 2
uv run pytest
uv run ruff check src tests scripts
```

---

### 12:45 · Clinical derisking product locked · Sameer + Codex

Scientific vertical finalized: clinical asset derisking for in vivo CRISPR,
focused on LNP delivery. Input is a clinical asset plus planned trial design;
output is a risk profile with safety, efficacy, confidence, FDA approval, and
commercial-success scores.

**Shipped:**
- `probception risk-profile` CLI
- deterministic clinical scoring in `clinical.py`
- responsive standalone `risk_report.html`
- seed trial records for Casgevy / exa-cel, VERVE-101, VERVE-102, NTLA-2001
- local Paperclip MCP bridge exposing search, trial gathering, and risk scoring
- resilient live adapter wrappers so failed integrations fall back cleanly

**Verified:**
```
probception risk-profile "VERVE-102 PCSK9 GalNAc-LNP" "Phase 1b/2..."
  → success 69.8, risk 30.2, status "advance with risk controls"

uv run pytest
  → 39 passed

uv run ruff check src tests scripts
  → clean
```

---

### DEC-7 · Integrations are accelerators, not single points of failure

**Decision.** Live partner tools are wrapped in deterministic fallbacks. Paperclip
retrieval tries SDK, CLI, then HTTP; live adapter failures degrade to mock
evidence or mock observations with the failure reason stored in metadata.

**Why.** A hackathon demo must survive conference wifi, account setup drift, API
shape changes, and expired credits. The scientific claim is the auditable loop,
not that every vendor endpoint is available every minute.

**Cost.** A fallback run is less scientifically rich than a live run. We make
that visible in metadata rather than pretending it was live.

---

### 11:30 · Boilerplate complete and pushed · Sameer + Claude

Repository initialised, core engine built, first push to
`sameernagar-hub/probception`.

**Shipped:**
- Bayesian belief state (Bayes, entropy, surprise) — deterministic, fully tested
- EIG planner with cost adjustment and a repetition discount
- Hash-chained append-only ledger with tamper detection
- Standalone zero-dependency HTML inspector
- Counterfactual replay harness + calibration scoring
- Paperclip and Proto adapters, plus mock/scripted adapters
- CLI: `doctor` · `demo` · `ask` · `counterfactual` · `score` · `report` · `verify` · `runs`
- 31 tests green, ruff clean

**Verified working end to end:**
```
probception demo            → resolved 0.104 bits over 3 experiments
probception counterfactual  → CLOSED LOOP, belief divergence 0.810
probception verify <run>    → 14 entries verified, chain intact
probception score <run>     → n=3, Brier 0.2532, top-1 66.7%
```

---

### DEC-1 · The LLM proposes; it never scores and never updates

**Decision.** Claude generates hypotheses and candidate experiments. Selection
(EIG ranking) and belief revision (Bayes) are pure deterministic functions with
no model in the path.

**Why.** Three things fall out of it: runs are reproducible; a wrong answer is
always traceable to either a bad hypothesis or a bad likelihood table rather than
to an unexaminable model decision; and swapping the reasoner becomes a clean
ablation that measures the model's actual contribution.

**Cost.** Less flexible than letting the model adjust beliefs directly. We think
that flexibility is precisely what we don't want.

---

### DEC-2 · Every state change writes to the ledger *before* it takes effect

**Decision.** Not "log important events" — every transition is recorded first.
Nothing mutates belief without a ledger entry.

**Why.** It is the difference between a log and a provenance record. It means a
completed run can be graded, replayed and audited entirely from disk with no live
model, which is what Track A's inspectability criterion is actually asking for.

**Cost.** Slightly more verbose code at each call site. Worth it.

---

### DEC-3 · Ship a deterministic reasoner alongside the LLM one

**Decision.** `HeuristicScientist` implements the same interface as
`LLMScientist` and needs no API key.

**Why.** Started as pragmatism — six people cloning a repo at a hackathon should
not each need a working API key to see the system run, and Anthropic credits are
capped at 200 claims event-wide. It turned out to be scientifically useful: it is
a genuine ablation arm that isolates how much of the result comes from Claude
versus from the Bayesian machinery. It also means the demo survives credit
exhaustion or wifi failure.

---

### DEC-4 · Add a repetition discount to the EIG planner

**Decision.** Utility is `EIG × 0.45^(times_run) / cost` rather than `EIG / cost`.

**Why.** Found by running the demo, not by theory. With pure `EIG/cost` the
planner picked the cheapest assay ("Negative control panel", cost 1.0) at *every
single step* — the utility ranking never changed because nothing about the
candidates changed. Bad demo, but more importantly bad science: EIG assumes
observations are conditionally independent given the hypothesis, and repeats of
the *same protocol* share systematic error, batch effects and reagent lot. The
second run genuinely tells you less than the first, and the model should say so.

**After the fix** the agent visibly explores — negative control, then high-power
replication, then back — and the trace shows *why* each switch happened.

**Honest caveat.** γ=0.45 is a judgement call, not a derivation. Modelling the
correlation between repeat runs explicitly is the principled version. Logged in
[ARCHITECTURE.md](ARCHITECTURE.md#known-limitations).

---

### DEC-5 · Make the counterfactual test fail loudly

**Decision.** `probception counterfactual` exits non-zero if the agent proposes
the same next experiment regardless of what the data said.

**Why.** This is the test we could most easily have quietly omitted or softened,
which is exactly why it should be the headline demo. An agent that claims to
close the loop should be willing to fail a test of whether it does.

---

### DEC-6 · Pin line endings to LF via `.gitattributes`

**Decision.** Force LF for all text files across the repo.

**Why.** Not cosmetic. Ledger entry ids are content hashes, so a file that
round-trips through CRLF on a Windows laptop and LF on a Mac produces different
ids for identical content — which would silently break reproducibility across a
team that is split between both.

---

### 09:35 · Lightning talks

_(fill in during the event — one line per tool on what its API actually gives us)_

- Paperclip:
- Proto:
- Modal:
- Benchling:

---

### 08:30 · Check-in

Arrived, credentials claimed. Everyone to run `probception doctor` before the
talks start.

**Credential status:**

| Person | Anthropic | Paperclip | Modal | Proto | Other |
|---|---|---|---|---|---|
| Stephen | | | | | |
| Anjane | | | | | |
| Kanishk | | | | | |
| Chaitra | | | | | |
| Kent | | | | | |
| Sameer | | | | | |

---

## Template for new entries

```markdown
### HH:MM · <what happened> · <author>

<what changed, in a sentence or two>

**Result:** <what actually came out — numbers if you have them>
```

For decisions:

```markdown
### DEC-n · <the decision, as a statement>

**Decision.** <what we're doing>
**Why.** <the reasoning — including what we're giving up>
**Cost.** <what this makes harder>
```

---

## Running experiment log

Record every real run here so results survive the person who ran them.

| Time | Run id | Question | Steps | Bits resolved | Verdict | Notes |
|---|---|---|---|---|---|---|
| 11:28 | `9cda8897d6` | (built-in demo question) | 3 | 0.104 | mock lab, offline reasoner | baseline smoke test |
| 11:29 | `cf-confirming` / `cf-refuting` | (built-in demo question) | 3 | — | **CLOSED LOOP**, divergence 0.810 | counterfactual proof |
| 12:45 | `risk_6ee1fdbbade2b5ba` | VERVE-102 PCSK9 GalNAc-LNP | — | — | success 69.8, risk 30.2 | clinical derisking smoke test |

---

## Open questions

Things we know we don't know. Cross out as they're resolved.

- [x] **What is the scientific question?** Clinical asset derisking for in vivo CRISPR, focused on LNPs.
- [ ] Where does the held-out data come from, and can we prove the agent never saw it?
- [ ] Do LLM-elicited likelihood tables survive contact with a domain expert?
- [x] Which single partner tool do we go deep on rather than wide across four? Paperclip for evidence; Proto/Modal/Tamarind remain execution follow-ons.
