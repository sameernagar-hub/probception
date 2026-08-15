# Architecture

Why Probception is built the way it is, and where to extend it.

---

## The central design decision

**The language model proposes. It never scores, and it never updates.**

```
Claude Opus 5                    Deterministic, tested, reproducible
─────────────                    ───────────────────────────────────
generate hypotheses      ──────▶  score by expected information gain
design experiments       ──────▶  select argmax utility
                                  execute against unseen data
                                  Bayes update
                                  write to hash-chained ledger
```

Everything on the right is arithmetic with unit tests. Everything on the left is
open-ended generation where a frontier model genuinely outperforms anything we
could hand-code.

**Why the split matters:**

1. **Reproducibility.** Given the same hypotheses and the same observations, the
   posterior is identical every time. If the LLM could nudge belief, no two runs
   would agree and no result would be checkable.
2. **Debuggability.** A wrong conclusion is always traceable to one of exactly
   two causes: a bad hypothesis, or a bad likelihood table. Both are visible in
   the ledger. There is no third category of "the model just decided that."
3. **Honest evaluation.** Because the machinery below is fixed, swapping the
   reasoner for the deterministic one is a clean ablation. It tells you how much
   of the result came from Claude versus from the Bayesian structure — a question
   most agent demos cannot answer about themselves.

If you are tempted to let the LLM adjust a posterior directly, that is the moment
to stop and open a discussion. It would make the system more flexible and
completely undermine its central claim.

---

## The loop

```
                ┌──────────────────────────────────────────┐
                │            Research question             │
                └────────────────────┬─────────────────────┘
                                     ▼
  ┌────────────┐   Evidence    ┌───────────┐   Hypotheses+priors  ┌──────────┐
  │  Retrieve  │──────────────▶│ Hypothesise│────────────────────▶│  Belief  │
  │ (Paperclip)│               │  (Claude)  │                     │  state   │
  └────────────┘               └───────────┘                      └────┬─────┘
                                                                       │
        ┌──────────────────────────────────────────────────────────────┘
        ▼
  ┌───────────┐  candidates  ┌──────────────┐  chosen   ┌──────────────┐
  │  Design   │─────────────▶│  Score: EIG  │──────────▶│   Execute    │
  │ (Claude)  │              │ per unit cost│           │ (Proto/ESM/…)│
  └───────────┘              └──────────────┘           └──────┬───────┘
        ▲                                                      │ observation
        │                    ┌──────────────┐                  │
        └────────────────────│ Bayes update │◀─────────────────┘
           belief changed    └──────┬───────┘
                                    │
                            every arrow writes first
                                    ▼
                        ┌───────────────────────┐
                        │ Hash-chained ledger   │──▶ HTML inspector
                        │ (append-only JSONL)   │──▶ Calibration + counterfactual
                        └───────────────────────┘
```

---

## The math, stated plainly

**Belief** is a probability distribution over mutually exclusive hypotheses.
Uncertainty is its Shannon entropy:

$$H(b) = -\sum_h b(h) \log_2 b(h)$$

**Expected information gain** of an experiment $e$ is how many bits of that
uncertainty we expect it to remove:

$$\text{EIG}(e) = H(b) - \sum_o P(o)\, H(b \mid o), \qquad P(o) = \sum_h b(h)\,P(o \mid h)$$

**The planner** maximises information per unit cost, discounted for repetition:

$$\text{utility}(e) = \frac{\text{EIG}(e) \cdot \gamma^{n_e}}{\text{cost}(e)}, \qquad \gamma = 0.45$$

**Why the repetition term exists.** EIG assumes observations are conditionally
independent given the hypothesis. For a *repeat of the same protocol* that is
false — systematic error, batch effects and a shared reagent lot are common to
both runs. Without this term the planner degenerates into running the single
cheapest assay forever, which is both bad science and, incidentally, a terrible
demo. We found this by running the loop and watching it happen.

**The update** is Bayes:

$$b'(h) \propto P(o \mid h)\, b(h)$$

**Surprise** — recorded at every step — is $-\log_2 P(o_{\text{observed}})$ under
the pre-observation prediction. It is the number that tells you when the agent
learned something it did not expect.

---

## Module responsibilities

| Module | Responsibility | LLM? | I/O? | Tested |
|---|---|---|---|---|
| `types.py` | Every contract, as a validated Pydantic model. Content-addressed ids. | no | no | via others |
| `belief/state.py` | Bayes, entropy, surprise, prediction | no | no | ✅ heavily |
| `design/eig.py` | EIG, novelty discount, cost-adjusted ranking | no | no | ✅ heavily |
| `agents/llm.py` | Claude wrapper: structured outputs, caching, tracing | **yes** | network | — |
| `agents/scientist.py` | Hypothesis + experiment generation; deterministic ablation arm | **yes** | no | via loop |
| `adapters/` | The *only* place that touches the outside world | no | network | via mocks |
| `trace/ledger.py` | Append-only hash-chained record | no | disk | ✅ incl. tamper detection |
| `trace/report.py` | Standalone HTML inspector | no | disk | ✅ |
| `eval/` | Calibration, counterfactual replay | no | disk | ✅ |
| `loop.py` | Orchestration | no | — | ✅ end-to-end |
| `cli.py` | Human interface | no | terminal | manual |

**The dependency rule:** `belief` and `design` import nothing from `agents` or
`adapters`. The math cannot become entangled with the model or the network. Keep
it that way.

---

## Provenance design

Three properties, each deliberate:

**1. Append-only.** Nothing is ever mutated. The ledger is the history, not a
snapshot of current state.

**2. Hash-chained.** Each entry's id is a hash of its own content *and* the
previous entry's id. Edit any earlier line and every subsequent `prev` stops
matching. `probception verify` re-walks the chain — we test that a tamper is
actually caught, because an integrity claim nobody tested is just marketing.

**3. Content-addressed evidence.** An `Evidence` id is a hash of its kind, source
and claim. Identical evidence always gets the same id; a citation cannot silently
drift from the thing it cites.

**The rule that makes it work:** *nothing changes belief without writing to the
ledger first.* Not "we log important events" — every state transition is written
before it takes effect. That is what allows a run to be graded, replayed and
audited from disk with no live model in the loop.

**What gets recorded per decision:** every candidate considered (not just the
winner), each one's EIG, cost, repetition count and utility, the predicted
outcome distribution *before* the result arrived, the observation, the surprise
in bits, and the full before/after posterior.

Recording the alternatives is the part that makes the trace genuinely
inspectable. "Why did you do that?" is only answerable if you can also see what
it declined to do.

---

## Validation design

Three layers, because any one alone is gameable.

**1. Calibration.** Predictions are recorded before outcomes arrive, so Brier and
log scores are computable from the ledger alone, against an explicit uninformed
baseline. `probception score` will tell you the agent is no better than chance if
that is true — the command is written to report it, not to hide it.

**2. Counterfactual replay.** The same agent, the same seed, the same reasoner,
run against worlds whose experiments return opposite results. Then diff the
proposal. `probception counterfactual` **exits non-zero** if the loop is open.
This is the test we could most easily have quietly omitted, which is exactly why
it is the headline demo.

**3. Ablation.** `HeuristicScientist` is a complete, deterministic reasoner
implementing the same interface. `--offline` swaps it in. Comparing the two
isolates the model's contribution from the Bayesian machinery's.

---

## Extension points

**Adding a scientific domain** — write a `SearchAdapter` and an
`ExperimentAdapter`. Nothing else. See [INTEGRATIONS.md](INTEGRATIONS.md).

**Adding a reasoning strategy** — implement `Scientist` (two methods) and pass it
to `ClosedLoop`. Useful for a domain-specific prompt, a fine-tuned model, or a
human-in-the-loop mode.

**Adding an evaluation** — read the ledger, return a report. `eval/calibration.py`
is 100 lines and is the template.

**Changing the planner** — `design/eig.py` is self-contained. Risk-averse
selection, budget constraints across a sequence, or non-myopic multi-step
lookahead all slot in here without touching anything else.

---

## Known limitations

Stated plainly, because a judge will find them and it is better if we found them
first.

| Limitation | Consequence | Would fix by |
|---|---|---|
| **Discrete hypotheses and outcomes** | Continuous quantities must be binned | Conjugate priors or a particle filter over a continuous parameter |
| **Fixed hypothesis space** | The agent cannot invent a hypothesis mid-run | Re-frame periodically; add a "none of the above" catch-all whose rising probability signals the space is wrong |
| **Likelihoods come from the LLM** | A confidently wrong likelihood table produces a confidently wrong posterior | This is the single biggest soundness risk. Mitigate by eliciting likelihoods from evidence, cross-checking across independent calls, and sensitivity analysis |
| **Myopic (one-step) planning** | May miss a sequence that is better jointly than greedily | Two-step lookahead; the EIG machinery already supports it |
| **Novelty discount is a heuristic** | γ=0.45 is judgement, not derivation | Model the correlation between repeat runs explicitly |
| **Cost is a scalar** | Real cost is time × reagents × instrument availability | Vector-valued cost with a budget constraint |

The likelihood-elicitation row is the one that matters most. Everything else is
an incremental improvement; that one is a genuine soundness question, and we
would rather say so than pretend the Bayesian framing makes the LLM's numbers
trustworthy on its own.

---

## Why not the obvious alternatives

**Why not a ReAct/tool-calling agent?** It would work and be faster to build, but
"why did you choose that tool call?" has no better answer than "the model decided
to." We would fail inspectability, which is a third of the rubric.

**Why not a vector database?** Evidence volume here is small; retrieval quality
is Paperclip's job. A vector DB would add a dependency, a service to run, and a
failure mode on conference wifi, in exchange for nothing.

**Why not an orchestration framework?** The loop is 200 lines and we understand
every one of them. At 2am on Sunday, debugging our own arithmetic beats
debugging someone's abstraction over it.

**Why is the report plain HTML instead of a dashboard?** Because it must open on
a laptop with no network, no server, and no build step, three minutes before a
demo. Every dependency is a liability under those conditions.
