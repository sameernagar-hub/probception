"""Render a run's ledger as a standalone HTML inspector.

No server, no CDN, no build step — one file you can open on the demo laptop or
email to a judge. This is the artefact that answers Track A's inspectability
criterion: every decision, the alternatives it beat, the evidence behind it, and
the belief trajectory, reconstructed from disk after the fact.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from probception.trace.ledger import Ledger

_CSS = """
:root{--bg:#0b0d10;--panel:#14181d;--line:#232a32;--fg:#e6edf3;--dim:#8b98a5;
--acc:#7cc7ff;--good:#4ade80;--warn:#fbbf24;--bad:#f87171;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.6 ui-sans-serif,-apple-system,Segoe UI,Roboto,sans-serif;padding:32px}
.wrap{max-width:1100px;margin:0 auto}
h1{font-size:26px;margin:0 0 4px} h2{font-size:17px;margin:32px 0 12px;color:var(--acc)}
.sub{color:var(--dim);margin-bottom:24px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;
padding:16px 18px;margin-bottom:14px}
.row{display:flex;gap:12px;flex-wrap:wrap}
.kpi{flex:1;min-width:150px;background:var(--panel);border:1px solid var(--line);
border-radius:10px;padding:14px 16px}
.kpi .v{font-size:22px;font-weight:600} .kpi .l{color:var(--dim);font-size:12px;
text-transform:uppercase;letter-spacing:.06em}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--dim);font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.05em}
.bar{height:7px;background:#1f2630;border-radius:4px;overflow:hidden;min-width:90px}
.bar > i{display:block;height:100%;background:var(--acc)}
.tag{display:inline-block;font-size:11px;padding:2px 7px;border-radius:999px;
border:1px solid var(--line);color:var(--dim);margin-right:5px}
.win{color:var(--good);font-weight:600}
code{background:#0f1318;padding:1px 5px;border-radius:4px;font-size:13px}
.mono{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12px;color:var(--dim)}
details{margin-top:8px} summary{cursor:pointer;color:var(--acc);font-size:13px}
pre{overflow-x:auto;background:#0f1318;padding:12px;border-radius:8px;font-size:12px}
.ok{color:var(--good)} .fail{color:var(--bad)}
"""


def _bar(p: float) -> str:
    return f'<div class="bar"><i style="width:{max(0.0, min(p, 1.0)) * 100:.1f}%"></i></div>'


def _esc(x) -> str:
    return html.escape(str(x))


def write_report(run_id: str, root: str | Path = "runs") -> Path:
    """Build `runs/<run_id>/report.html` from the ledger. Returns its path."""
    ledger = Ledger.load(run_id, root)
    entries = ledger.read()
    if not entries:
        raise FileNotFoundError(f"No ledger entries for run {run_id}")

    intact, chain_msg = ledger.verify()
    started = next((e for e in entries if e["event"] == "run_started"), {"payload": {}})
    finished = next((e for e in entries if e["event"] == "run_finished"), None)
    evidence = next((e for e in entries if e["event"] == "evidence_gathered"), {"payload": []})
    framed = next((e for e in entries if e["event"] == "hypotheses_framed"), {"payload": {}})
    scored = [e for e in entries if e["event"] == "experiments_scored"]
    updates = [e for e in entries if e["event"] == "belief_updated"]
    proposal = next((e for e in entries if e["event"] == "next_experiment_proposed"), None)
    calls = [e for e in entries if e["event"] == "model_call"]

    q = started["payload"].get("question", "(unknown question)")
    summary = finished["payload"] if finished else {}
    h0 = summary.get("entropy_start", framed["payload"].get("prior_entropy_bits", 0.0))
    h1 = summary.get("entropy_end", 0.0)
    resolved = max(h0 - h1, 0.0)

    parts: list[str] = [
        "<!-- Probception run inspector -->",
        f"<style>{_CSS}</style>",
        '<div class="wrap">',
        f"<h1>Probception &mdash; run <code>{_esc(run_id)}</code></h1>",
        f'<div class="sub">{_esc(q)}</div>',
        '<div class="row">',
        f'<div class="kpi"><div class="l">Uncertainty resolved</div>'
        f'<div class="v">{resolved:.2f} bits</div></div>',
        f'<div class="kpi"><div class="l">Entropy</div>'
        f'<div class="v">{h0:.2f} &rarr; {h1:.2f}</div></div>',
        f'<div class="kpi"><div class="l">Experiments run</div>'
        f'<div class="v">{len(updates)}</div></div>',
        f'<div class="kpi"><div class="l">Ledger integrity</div>'
        f'<div class="v {"ok" if intact else "fail"}">{"intact" if intact else "BROKEN"}</div></div>',
        "</div>",
        f'<div class="mono" style="margin-top:8px">{_esc(chain_msg)} &middot; '
        f"reasoner: {_esc(started['payload'].get('reasoner'))} &middot; "
        f"lab: {_esc(started['payload'].get('lab'))} &middot; "
        f"mode: {_esc(started['payload'].get('mode'))}</div>",
    ]

    # Final belief
    if summary.get("final_belief"):
        parts.append("<h2>Where the agent ended up</h2><div class='card'><table>")
        parts.append("<tr><th>Hypothesis</th><th>Posterior</th><th></th></tr>")
        for stmt, p in sorted(summary["final_belief"].items(), key=lambda kv: -kv[1]):
            parts.append(
                f"<tr><td>{_esc(stmt)}</td><td>{p:.3f}</td><td>{_bar(p)}</td></tr>"
            )
        parts.append("</table></div>")

    # Decision trail
    parts.append("<h2>Decision trail</h2>")
    for i, ev in enumerate(scored):
        payload = ev["payload"]
        chosen = payload["chosen"]
        upd = updates[i]["payload"] if i < len(updates) else None
        parts.append('<div class="card">')
        parts.append(f"<b>Step {i + 1}</b> &mdash; scored {len(payload['candidates'])} candidates")
        parts.append("<table><tr><th>Experiment</th><th>EIG (bits)</th><th>Cost</th>"
                     "<th>Times run</th><th>Utility</th><th>Predicted</th></tr>")
        for c in payload["candidates"]:
            win = ' class="win"' if c["id"] == chosen else ""
            pred = ", ".join(f"{k} {v:.2f}" for k, v in c["predicted_outcomes"].items())
            mark = " &#9679;" if c["id"] == chosen else ""
            ran = c.get("times_run", 0)
            ran_cell = f"{ran}x (x{c.get('novelty', 1):.2f})" if ran else "&mdash;"
            parts.append(
                f"<tr{win}><td>{_esc(c['title'])}{mark}</td><td>{c['eig_bits']:.3f}</td>"
                f"<td>{c['cost']:.1f}</td><td class='mono'>{ran_cell}</td>"
                f"<td>{c['utility']:.3f}</td>"
                f"<td class='mono'>{_esc(pred)}</td></tr>"
            )
        parts.append("</table>")
        if upd:
            parts.append(
                f"<div style='margin-top:10px'>Observed <code>{_esc(upd['observed'])}</code> "
                f"&middot; surprise <b>{upd['surprise_bits']:.2f} bits</b> "
                f"&middot; entropy {upd['entropy_before_bits']:.3f} &rarr; "
                f"{upd['entropy_after_bits']:.3f} "
                f"&middot; leader: {_esc(upd['leader'])}</div>"
            )
        parts.append("</div>")

    # Terminal proposal
    if proposal:
        p = proposal["payload"]
        parts.append(
            "<h2>What it proposes next</h2>"
            f"<div class='card'><b>{_esc(p['title'])}</b> "
            f"<span class='tag'>{p['eig_bits']:.3f} bits</span>"
            f"<div style='margin-top:8px'>{_esc(p['protocol'])}</div>"
            f"<div class='mono' style='margin-top:8px'>{_esc(p['rationale'])}</div></div>"
        )

    # Evidence
    ev_items = evidence["payload"] if isinstance(evidence["payload"], list) else []
    if ev_items:
        parts.append("<h2>Evidence base</h2><div class='card'><table>")
        parts.append("<tr><th>ID</th><th>Kind</th><th>Source</th><th>Claim</th><th>Strength</th></tr>")
        for e in ev_items:
            parts.append(
                f"<tr><td class='mono'>{_esc(e['id'])}</td><td>{_esc(e['kind'])}</td>"
                f"<td class='mono'>{_esc(e['source'])}</td><td>{_esc(e['claim'])}</td>"
                f"<td>{e.get('strength', 0):.2f}</td></tr>"
            )
        parts.append("</table></div>")

    # Model calls
    if calls:
        total_in = sum((c["payload"]["usage"].get("input_tokens") or 0) for c in calls)
        total_out = sum((c["payload"]["usage"].get("output_tokens") or 0) for c in calls)
        cached = sum((c["payload"]["usage"].get("cache_read_input_tokens") or 0) for c in calls)
        parts.append(
            f"<h2>Model usage</h2><div class='card'>{len(calls)} calls &middot; "
            f"{total_in:,} input / {total_out:,} output tokens &middot; "
            f"{cached:,} read from cache</div>"
        )

    # Raw ledger
    parts.append(
        "<h2>Raw ledger</h2><div class='card'><details><summary>"
        f"Show all {len(entries)} hash-chained entries</summary>"
        f"<pre>{_esc(json.dumps(entries, indent=2)[:200000])}</pre></details></div>"
    )
    parts.append("</div>")

    out = Path(root) / run_id / "report.html"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out
