# Probception — notes for Claude Code

Read this before changing anything. It captures the constraints that make this
codebase work; violating them silently breaks the project's central claim.

## What this is

A Bayesian optimal-experimental-design agent. It holds explicit beliefs over
competing hypotheses, picks the experiment with the highest expected information
gain per unit cost, runs it against unseen data, and applies Bayes. Built for
re:AGENT Track A.

## The rule that matters most

**The LLM proposes. It never scores, and it never updates.**

Claude generates hypotheses and candidate experiments. Selection (`design/eig.py`)
and belief revision (`belief/state.py`) are pure deterministic functions with no
model in the path.

If you are about to let a model adjust a posterior, set a utility, or decide a
ranking — **stop and ask the user first.** That change would make runs
irreproducible and decisions unauditable, which defeats the point of the project.

## Architectural constraints

1. **`belief/` and `design/` import nothing from `agents/` or `adapters/`.** The
   math must not become entangled with the model or the network. Check this
   before adding an import.
2. **Nothing changes belief without writing to the ledger first.** Not "log
   important things" — every state transition is recorded before it takes effect.
3. **All external I/O goes through `adapters/`.** No `httpx` calls anywhere else.
4. **`outcome_label` must be one of the experiment's declared outcomes.** The
   Bayes update indexes the likelihood table by that string; a new label silently
   corrupts the posterior.
5. **Thresholds that discretise a continuous score go in `experiment.params`,**
   so they are ledgered before the job runs. Goalposts must not move after
   results are seen.
6. **The HTML report must contain no external references.** There is a test
   asserting no `http://` or `https://` appears in it. It has to open on a laptop
   with no network.

## Commands

```bash
uv run pytest                        # 31 tests, ~1s
uv run ruff check src tests          # must be clean
uv run probception doctor            # environment check
uv run probception demo              # full loop, no API key needed
uv run probception counterfactual    # the closing-the-loop proof; exits 1 if open
```

**Both tests and ruff must pass before any commit.**

## Layout

```
src/probception/
├── types.py           Pydantic contracts, content-addressed ids
├── belief/state.py    Bayes, entropy, surprise      — pure, heavily tested
├── design/eig.py      EIG, novelty discount, ranking — pure, heavily tested
├── agents/llm.py      Claude wrapper (structured outputs, caching, tracing)
├── agents/scientist.py LLM reasoner + deterministic ablation arm
├── adapters/          The only I/O boundary
├── trace/             Hash-chained ledger + standalone HTML inspector
├── eval/              Calibration + counterfactual harness
├── loop.py            Orchestration
└── cli.py             Typer CLI
```

## Conventions

- Python 3.11+, `from __future__ import annotations`, full type hints
- Pydantic v2 for every data contract — not dataclasses, not dicts
- Line length 100, ruff-enforced
- Comments explain **why**, never what. If a line needs a comment saying what it
  does, rename something instead.
- Docstrings on modules and non-obvious functions; skip them on trivial ones
- Tests name the behaviour they protect:
  `test_uninformative_experiment_leaves_belief_untouched`, not `test_update_2`

## Things that will bite you

- **Adding a dependency.** Every one is a failure mode on conference wifi. The
  bar is high — ask first.
- **`effort` and `output_format` together.** Some SDK versions reject the
  combination; `agents/llm.py` falls back gracefully. Don't remove that handling.
- **Line endings.** `.gitattributes` pins LF because ledger ids are content
  hashes. Don't override it.
- **The novelty discount** (`design/eig.py`) exists because without it the
  planner picks the cheapest assay forever. Don't "simplify" it away.

## Current state

Boilerplate complete, all tests green, demo and counterfactual verified.
The scientific question is deliberately still open — the architecture is
domain-agnostic, so science plugs in via adapters without touching the loop.
