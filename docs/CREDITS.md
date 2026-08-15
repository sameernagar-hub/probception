# Credits, attribution, and what we depend on

---

## The event

**re:AGENT** — a two-day build weekend on the infrastructure scientific agents
still need: better datasets, sharper tools, and reliable ways to evaluate their
work. 15–16 August 2026, 2 Marina Boulevard, Building C.

Probception was built there, for **Track A — Build an AI Scientist**.

### Co-hosts

**GXL** · **Arc Institute** · **Anthropic** · **BenchFlow** · **future.bio** · **Biohub**

### Sponsors

**Founders Inc** · **LatchBio** · **Boltz** · **Modal** · **Benchling** · **Strand AI**

Thank you for the compute, the credits, the food, and — more valuably — for
having your engineers in the room to answer questions.

---

## Tools we build on

| Tool | Provided by | What it does for us |
|---|---|---|
| **Claude Opus 5** | Anthropic | Hypothesis generation and experiment design under a falsifiability contract |
| **Paperclip** | GXL | Agent-native access to papers, datasets, trials and biological databases — our evidence layer |
| **Proto** | re:AGENT partners | Generative biological design, treated as an experiment with pre-declared outcomes |
| **Modal** | Modal | The compute substrate for anything needing a GPU |
| **ESM** | Meta AI (via the open ecosystem) | Protein language model representations |
| **Boltz** | Boltz | Structure prediction |
| **Tamarind** | Tamarind Bio | Hosted bioinformatics jobs — our cheapest orthogonal readout |
| **Benchling** | Benchling | LIMS + MCP server; the bridge to real wet-lab reality |
| **Phylo / Biomni** | Phylo Bio | Biomedical agent platform, used as a comparison baseline |

Credit redemption instructions for each: **[INTEGRATIONS.md](INTEGRATIONS.md)**.

---

## Software dependencies

Deliberately few. Every dependency is a thing that can fail on conference wifi
three minutes before a demo.

### Runtime

| Package | Licence | Why it's here |
|---|---|---|
| [`anthropic`](https://github.com/anthropics/anthropic-sdk-python) | MIT | Official Claude SDK — structured outputs, prompt caching |
| [`pydantic`](https://github.com/pydantic/pydantic) | MIT | Every contract is a validated model; also generates the LLM output schemas |
| [`typer`](https://github.com/fastapi/typer) | MIT | CLI |
| [`rich`](https://github.com/Textualize/rich) | MIT | Terminal output that reads well in a live demo |
| [`httpx`](https://github.com/encode/httpx) | BSD-3 | HTTP for adapters |
| [`python-dotenv`](https://github.com/theskumar/python-dotenv) | BSD-3 | `.env` loading |
| [`numpy`](https://github.com/numpy/numpy) | BSD-3 | Numerics |

### Development

| Package | Licence | Why |
|---|---|---|
| [`pytest`](https://github.com/pytest-dev/pytest) | MIT | Tests |
| [`ruff`](https://github.com/astral-sh/ruff) | MIT | Lint + format |
| [`uv`](https://github.com/astral-sh/uv) | Apache-2.0 / MIT | Reproducible installs, Python version management |
| [`hatchling`](https://github.com/pypa/hatch) | MIT | Build backend |

### What we deliberately did *not* use

- **No vector database.** Evidence volume is small and retrieval quality is
  Paperclip's job. A vector DB would add a service to run and a failure mode, for
  nothing.
- **No agent orchestration framework.** The loop is ~200 lines we fully
  understand. At 2am, debugging our own arithmetic beats debugging an abstraction
  over it.
- **No web framework or dashboard.** The inspector is one self-contained HTML
  file so it opens with no server, no build step, and no network.
- **No CDN, webfont, or external asset anywhere.** Tested: the report contains no
  `http://` or `https://` references at all, and there's a unit test asserting it.

---

## Intellectual credit

The ideas Probception assembles are not ours; the assembly is.

- **Bayesian optimal experimental design** — the expected-information-gain
  criterion traces to Lindley (1956), *On a Measure of the Information Provided
  by an Experiment*, building on Shannon (1948).
- **Information theory** — Shannon, *A Mathematical Theory of Communication* (1948).
- **Calibration and proper scoring rules** — Brier (1950); the broader literature
  on why a forecaster's confidence should be checkable against outcomes.
- **Active learning / sequential design** — the large body of work on choosing
  the next query to maximise information.
- **Hash-chained append-only logs** — a standard construction from tamper-evident
  logging and distributed systems.

What we claim as our contribution is putting these together *around* a frontier
language model in a way where the model does the creative work and the classical
machinery does the accounting — and then building the tooling that makes the
resulting agent auditable and falsifiable.

---

## The team

Stephen · Anjane · Kanishk · Chaitra · Kent · Sameer

---

## Licence

MIT — see [LICENSE](../LICENSE). Take it, fork it, point it at your own science.

Per the re:AGENT FAQ, teams keep what they build. We would rather this be useful
to someone than sit in a private repo.
