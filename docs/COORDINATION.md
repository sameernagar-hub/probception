# Team coordination

Six people, ~26 hours, one repo. This document exists so nobody has to ask
"what should I be doing?" or "can I push this?"

**Team:** Stephen · Anjane · Kanishk · Chaitra · Kent · Sameer
**Event:** re:AGENT, 2 Marina Boulevard, Building C, 3rd floor (left out of the lift)
**Repo:** https://github.com/sameernagar-hub/probception
**Track:** A — Build an AI Scientist

---

## The one thing to internalise

**The reasoning core is done and it is domain-agnostic.** Nobody needs to touch
`belief/`, `design/`, or `trace/` to add science. You add science by writing an
**adapter** and a **question**. If you find yourself editing the Bayes update to
make your feature work, stop and ask in the channel — you have almost certainly
found a seam we should design properly instead.

---

## Lanes

Six people on one repo goes wrong when two people edit the same file. These
lanes are drawn so that they mostly don't. **Claim yours by editing this table
and pushing** — first come, first served.

| Lane | Owns these files | Deliverable | Owner |
|---|---|---|---|
| **A. Science question** | `docs/QUESTION.md`, the eval dataset | The actual scientific question + a held-out set the agent has never seen | _unclaimed_ |
| **B. Evidence / Paperclip** | `adapters/paperclip.py` | Real retrieval feeding real priors | _unclaimed_ |
| **C. Design / execution** | `adapters/proto.py`, `adapters/esm.py`, Modal jobs | An experiment that actually runs on real infrastructure | _unclaimed_ |
| **D. Reasoning quality** | `agents/scientist.py`, prompts | Hypotheses and likelihood tables a scientist would sign off on | _unclaimed_ |
| **E. Evaluation** | `eval/`, `tests/` | The validation story: calibration, ablation, retrodiction | _unclaimed_ |
| **F. Demo & narrative** | `trace/report.py`, `docs/DEMO.md`, slides | The 3 minutes that decide the outcome | _unclaimed_ |

**Two people can share a lane. Nobody should be in three.**

If your lane is blocked, take the highest-value unclaimed task rather than
inventing work in someone else's files.

---

## Git protocol

Deliberately lightweight. We are optimising for merge frequency, not process.

```bash
git checkout -b <yourname>/<short-thing>     # e.g. sameer/paperclip-adapter
# ... work ...
uv run pytest && uv run ruff check src tests  # both must pass
git add -A && git commit -m "..."
git push -u origin <yourname>/<short-thing>
gh pr create --fill
```

**Rules:**

1. **Never push directly to `main`.** One exception: fixing a broken `main`.
2. **Merge at least every 3 hours.** A branch that lives longer than one build
   session is a merge conflict waiting for the worst possible moment.
3. **Tests and lint pass before you open a PR.** No exceptions — CI enforces it.
4. **Any teammate can approve.** Do not wait for a specific person. A 5-minute
   review by whoever is free beats a 40-minute wait for the "right" reviewer.
5. **If `main` is broken, fixing it is everyone's top priority.** Drop what you
   are doing.

**Commit messages:** say what changed and why. `fix stuff` costs the next person
ten minutes of `git log` archaeology.

---

## Schedule — Day 1, Saturday 15 August

| Time | What | Team focus |
|---|---|---|
| 8:30–9:15 | Check-in, coffee | Everyone runs `probception doctor` on their laptop **before** the talks |
| 9:15–9:35 | Welcome & overview | — |
| 9:35–10:25 | Host tool lightning talks | **Take notes on Paperclip + Proto APIs.** Assign one person per tool. |
| 10:25–12:10 | Track ideation, team formation, setup | **Lock the scientific question. This is the highest-leverage hour of the weekend.** Claim lanes above. |
| 12:10–1:00 | Lunch | Sanity-check the question against someone from a partner team |
| 1:00–3:30 | **Build I** | Adapters wired. Goal: `probception ask "<our question>"` runs against one real tool. |
| 3:30–6:30 | **Build II** | Real experiments executing. Goal: a full loop on real data end to end. |
| 6:30–7:15 | Dinner | — |
| 7:15–9:45 | **Build III** | Evaluation + counterfactual on the real question. Goal: the validation story holds. |
| 9:45–10:15 | Overnight experiment checkpoint | **Launch anything long-running now** — Modal jobs, design campaigns |
| 10:15–11:00 | Day 1 close | Demo dry-run #1. Whatever exists, present it to each other. |

## Schedule — Day 2, Sunday 16 August

| Time | What | Team focus |
|---|---|---|
| 8:30–9:00 | Doors reopen | Collect overnight results |
| 9:00–10:45 | **Final build** | **Feature freeze at 10:00.** Last 45 min is demo rehearsal only. |
| **10:45** | **SUBMISSION DEADLINE** | Non-negotiable |
| 10:45–11:30 | Brunch, expo, demo checks | Test the demo on the actual presentation setup |
| 11:30–12:30 | Featured panel | Rest. Do not code. |
| 12:30–2:00 | **Project demos & live judging** | — |
| 2:00–2:20 | Scoring & awards | — |

### Hard checkpoints

- **Saturday 12:10 — question locked.** If we are still debating at lunch, we
  take the best option on the table and commit. A mediocre question executed
  well beats a great question started at 4pm.
- **Saturday 21:45 — overnight jobs launched.** Anything needing >1h of compute
  goes now or does not happen.
- **Sunday 10:00 — feature freeze.** No new code after this. Only fixes to
  things that break during rehearsal.
- **Sunday 10:45 — submitted.** Submit at 10:30 with something imperfect rather
  than at 10:46 with something perfect.

---

## Demo plan (3 minutes, rehearsed)

The demo is a deliverable, not an afterthought. Rehearse it **three times**.

| Time | Beat | Command |
|---|---|---|
| 0:00–0:25 | **The problem.** "Agents give you confident paragraphs. You can't tell what they actually know." | — |
| 0:25–1:10 | **The loop.** Show it framing hypotheses and choosing an experiment by information gain — including *rejecting* a more expensive, more impressive one. | `probception ask "<question>"` |
| 1:10–1:50 | **Closing the loop.** Same agent, opposite results, different next experiment. | `probception counterfactual` |
| 1:50–2:30 | **Inspectability.** Open the HTML report. Every candidate, every prediction, every update. Then prove the ledger can't be forged. | `probception verify <run>` |
| 2:30–3:00 | **Validation + the ask.** Calibration numbers, the ablation arm, and what we'd do with another week. | `probception score <run>` |

**Demo hygiene:**
- Pre-record a screen capture as backup. **Conference wifi will fail.**
- Have a `runs/` directory with a good completed run already in it.
- The HTML inspector is fully offline by design — it will work with wifi down.
- Never live-code during a demo. Never.

---

## Working agreements

- **Ask for help at 10 minutes.** Not 40. Nobody gets points for suffering quietly.
- **Push working code often.** A broken laptop at 11pm should cost us one commit, not one lane.
- **Negative results are results.** If the counterfactual shows the loop is open,
  or calibration is no better than chance, **we report it**. Judges have seen a
  hundred demos that quietly hide the failing metric; a team that shows its own
  failure and explains it is more credible, not less. This is also just how
  science works.
- **No secrets in git.** Ever. `.env` is gitignored. If you commit a key by
  accident, say so immediately and we rotate it — that is not embarrassing, a
  silently leaked key is.
- **Sleep.** A rested person on Sunday morning is worth two exhausted ones.

---

## Communication

- **Team channel** — default. Ask here first.
- **re:AGENT Discord** — https://discord.gg/6ub6CQvmnA — partner support. If
  Paperclip or Proto misbehaves, ask there; their engineers are live and on-site.
- **GXL Paperclip Slack** — for Paperclip specifics.
- **In person** — you are all in the same room. Walk over. It is faster.

---

## If we fall behind

Cut in this order. Decided now, calmly, so we don't debate it at 2am:

1. **Cut** extra adapters. One real tool used well beats four wired shallowly.
2. **Cut** the live scientific dataset — fall back to the scripted world. The
   counterfactual proof still works and is still the strongest thing we have.
3. **Cut** additional experiment types. Two discriminating experiments are enough
   to demonstrate the loop.
4. **Never cut** the counterfactual demo, the ledger, or the HTML inspector.
   Those three *are* the submission. Everything else is supporting material.
