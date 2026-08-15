# Setup

Get from a fresh laptop to a running closed loop. **Target: 10 minutes.**

Everything here works on **macOS**, **Windows**, and **Linux**. The demo runs
with **zero API keys** — get that working first, add credentials second.

---

## 0. What you need before you start

| Requirement | Why | Check |
|---|---|---|
| **Python 3.11–3.13** | The core language. 3.12 is what we pin. | `python --version` |
| **Git** | Obviously. | `git --version` |
| **A GitHub account with access to the repo** | To push. | `git ls-remote https://github.com/sameernagar-hub/probception` |
| **uv** (recommended) | Fast, reproducible installs. Replaces pip + venv. | `uv --version` |

> **Why Python 3.12 and not 3.13/3.14?** Scientific wheels (Biopython, torch,
> anything ESM-adjacent) lag new Python releases by months. On hackathon wifi you
> do not want to discover this by watching a package build from source. If your
> system Python is newer, `uv` will fetch 3.12 for you — you do not need to
> uninstall anything.

---

## 1. Install `uv`

**macOS / Linux**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell)**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Homebrew (macOS), if you prefer**
```bash
brew install uv
```

Close and reopen your terminal, then confirm:
```bash
uv --version
```

<details>
<summary><b>No uv? Plain pip works too.</b></summary>

```bash
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
```
Everywhere below that says `uv run probception`, use `probception` instead
(with the venv activated).
</details>

---

## 2. Clone and install

```bash
git clone https://github.com/sameernagar-hub/probception
cd probception
uv sync --extra dev
```

`uv sync` creates `.venv/`, fetches Python 3.12 if you don't have it, and installs
everything. It does not touch your system Python.

---

## 3. Verify the machine

```bash
uv run probception doctor
```

You should see green for Python and every package. Credentials will show as
`unset` — that is expected and fine.

---

## 4. Run the loop

```bash
uv run probception demo
```

You will see the agent frame hypotheses, score candidate experiments by
information gain, run one, and update its beliefs. It ends by printing a path to
a **standalone HTML inspector** — open it.

**macOS**
```bash
open runs/<run-id>/report.html
```
**Windows**
```powershell
start runs\<run-id>\report.html
```
**Linux**
```bash
xdg-open runs/<run-id>/report.html
```

Then run the one that actually proves the thing:

```bash
uv run probception counterfactual
```

**If this prints `CLOSED LOOP`, your setup is correct and complete.**

Run the clinical derisking pre-phase demo:

```bash
uv run probception risk-profile "VERVE-102 PCSK9 GalNAc-LNP" `
  "Phase 1b/2 single ascending dose in HeFH or premature CAD; endpoints: safety, PCSK9, LDL-C"
```

On macOS/Linux, replace the PowerShell backtick with `\`. This command writes a
responsive HTML report under `runs/<risk-id>/risk_report.html` and works even
with no live integrations configured.

---

## 5. Run the tests

```bash
uv run pytest
uv run ruff check src tests
```

39 tests, all green, in a few seconds. If they pass, you can start writing
code with confidence that you'll know when you break something.

---

## 6. Add credentials (when you need them)

Copy the template:

**macOS / Linux**
```bash
cp .env.example .env
```
**Windows**
```powershell
Copy-Item .env.example .env
```

Then open `.env` and fill in what you have. **`.env` is gitignored — never commit it.**

Start with just this one:

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

Re-run `uv run probception doctor` — it should now show `set`, and `demo` will
use Claude for hypothesis generation instead of the offline reasoner.

Where each key comes from: **[INTEGRATIONS.md](INTEGRATIONS.md)**.

To switch from mock adapters to live ones:
```bash
PROBCEPTION_MODE=live
```

Live mode is intentionally resilient. If Paperclip, Proto, Modal, Tamarind, or
another partner tool fails, Probception falls back to deterministic local
evidence or mock execution and records the failure reason in returned metadata.
The demo should degrade, not crash.

### Paperclip MCP

For clients that support remote MCP, configure:

```json
{
  "mcpServers": {
    "paperclip": {
      "type": "http",
      "url": "https://paperclip.gxl.ai/mcp",
      "headers": {
        "X-API-Key": "${PAPERCLIP_API_KEY}"
      }
    }
  }
}
```

For a local stdio bridge with deterministic fallbacks:

```bash
uv run python scripts/paperclip_mcp.py
```

See `.mcp.example.json`.

---

## Platform notes

### Windows

- **Use PowerShell, not cmd.exe.** Some commands below assume it.
- If `.venv\Scripts\Activate.ps1` is blocked:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```
- If `python` opens the Microsoft Store, that's the App Execution Alias stub.
  Either install real Python from python.org, or just use `uv run` for
  everything and ignore it.
- Long paths: if you hit a path-length error installing scientific packages,
  enable long paths once as Administrator:
  ```powershell
  New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
    -Name LongPathsEnabled -Value 1 -PropertyType DWORD -Force
  ```

### macOS

- On Apple Silicon everything here is native arm64. No Rosetta needed.
- If you later add `torch` for ESM work, install the MPS build, not CPU-only.
- Xcode command line tools if `git` prompts: `xcode-select --install`

### Linux

- You may need `build-essential` and `python3-dev` for scientific extras:
  ```bash
  sudo apt install -y build-essential python3-dev
  ```

---

## Optional extras (only when a task needs them)

These are **not** installed by default — they are heavy and most of the team
will never need them.

```bash
uv sync --extra bio       # Biopython — sequence handling
uv sync --extra compute   # Modal — remote GPU jobs
```

For Modal, after installing:
```bash
uv run modal setup
```
This opens a browser and writes your tokens. Claim credits first at
`modal.fillout.com/t/qMXCmRGseUus`.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `probception: command not found` | Not using `uv run`, or venv not active | Prefix with `uv run`, or activate `.venv` |
| `ModuleNotFoundError: probception` | Installed without `-e`, or wrong directory | `cd` to repo root, `uv sync --extra dev` |
| `No ANTHROPIC_API_KEY found` | Expected without a key | Harmless. The loop still runs offline. |
| `doctor` shows a package missing | Install didn't finish | `uv sync --extra dev` again |
| Tests fail on a fresh clone | Almost always a stale venv | Delete `.venv`, then `uv sync --extra dev` |
| Paperclip search fails | CLI/auth/API outage | The clinical demo falls back to seed trials; check `PAPERCLIP_API_KEY` later |
| Proto job fails | Endpoint/credit/job issue | Live lab falls back to deterministic mock observation with the error in metadata |
| `counterfactual` exits 1 | The loop genuinely is not closing | That's a real bug — read the printed notes, don't ignore it |
| Weird diffs on every file | Line-ending drift | `.gitattributes` handles this; run `git add --renormalize .` |
| SSL errors on conference wifi | Captive portal | Open a browser, accept the portal, retry |

Still stuck: post in the team Discord channel with the full output of
`uv run probception doctor`. Do not debug alone for more than 10 minutes —
that's the rule.

---

## For teammates using Claude Code

The repo ships a `CLAUDE.md` at the root. Claude Code reads it automatically and
will pick up the project conventions, the architecture, and the rule that the
LLM layer never touches belief updates. You don't need to explain the codebase
to it each time.
