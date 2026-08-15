"""Probception command line.

    probception doctor        check this machine is ready
    probception demo          run the closed loop end to end (no API key needed)
    probception ask "..."     run the loop on your own question
    probception counterfactual  prove the loop actually closes
    probception score <run>   grade a finished run's calibration
    probception report <run>  rebuild the HTML inspector
    probception verify <run>  re-walk the ledger hash chain
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from probception import __version__
from probception.adapters import get_lab, get_searcher
from probception.agents.llm import Claude
from probception.agents.scientist import HeuristicScientist, LLMScientist, Scientist
from probception.clinical import score_asset, write_risk_report
from probception.config import settings
from probception.eval.calibration import score_run
from probception.eval.counterfactual import World, run_counterfactual
from probception.loop import ClosedLoop
from probception.trace.ledger import Ledger
from probception.trace.report import write_report

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="An AI scientist that runs the experiment most likely to prove itself wrong.",
)
console = Console()

DEFAULT_QUESTION = (
    "Do protein language model embeddings predict stability effects of point "
    "mutations well enough to replace a wet-lab pre-screen?"
)


def _pick_scientist(force_heuristic: bool = False) -> Scientist:
    """Use Claude when a key is present; fall back to the deterministic reasoner."""
    if force_heuristic:
        return HeuristicScientist()
    claude = Claude()
    if claude.available:
        return LLMScientist(claude)
    console.print(
        "[yellow]No ANTHROPIC_API_KEY found — using the deterministic reasoner.[/yellow] "
        "The full loop still runs; only hypothesis generation is offline."
    )
    return HeuristicScientist()


def _belief_table(belief: dict[str, float], title: str) -> Table:
    table = Table(title=title, show_lines=False, title_justify="left")
    table.add_column("Hypothesis", overflow="fold")
    table.add_column("p", justify="right", width=7)
    table.add_column("", width=22)
    for stmt, p in sorted(belief.items(), key=lambda kv: -kv[1]):
        bar = "█" * max(int(p * 20), 0)
        table.add_row(stmt, f"{p:.3f}", f"[cyan]{bar}[/cyan]")
    return table


@app.command()
def version() -> None:
    """Print the version."""
    console.print(f"probception {__version__}")


@app.command()
def doctor() -> None:
    """Check this machine has what it needs. Run this first."""
    console.print(Panel.fit("[bold]Probception environment check[/bold]", border_style="cyan"))

    table = Table(show_header=True)
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail", overflow="fold")

    py_ok = sys.version_info >= (3, 11)
    table.add_row(
        "Python >= 3.11",
        "[green]ok[/green]" if py_ok else "[red]too old[/red]",
        f"{sys.version.split()[0]}",
    )

    for module in ("anthropic", "pydantic", "httpx", "rich", "typer", "numpy"):
        try:
            __import__(module)
            table.add_row(f"package: {module}", "[green]ok[/green]", "")
        except ImportError:
            table.add_row(f"package: {module}", "[red]missing[/red]", "run: uv sync")

    for name, present, where in settings.credential_report():
        table.add_row(
            f"env: {name}",
            "[green]set[/green]" if present else "[yellow]unset[/yellow]",
            "" if present else f"get it at {where}",
        )

    table.add_row("mode", f"[cyan]{settings.mode}[/cyan]", "mock runs with zero credentials")
    table.add_row("model", f"[cyan]{settings.model}[/cyan]", f"effort={settings.effort}")
    console.print(table)

    if not settings.has_claude:
        console.print(
            "\n[yellow]No Claude key yet.[/yellow] Everything below still works:\n"
            "  [bold]probception demo[/bold]           full loop, offline reasoner\n"
            "  [bold]probception counterfactual[/bold] the closing-the-loop proof\n"
        )
    else:
        console.print("\n[green]Ready.[/green] Try: [bold]probception demo[/bold]")


@app.command()
def demo(
    steps: int = typer.Option(3, help="How many experiments to run."),
    offline: bool = typer.Option(False, "--offline", help="Force the deterministic reasoner."),
) -> None:
    """Run the whole loop on a built-in question. Works with no API key."""
    ask(question=DEFAULT_QUESTION, steps=steps, offline=offline, candidates=4)


@app.command()
def ask(
    question: str = typer.Argument(..., help="The scientific question to investigate."),
    steps: int = typer.Option(3, help="How many experiments to run."),
    candidates: int = typer.Option(4, help="Candidate experiments designed per step."),
    offline: bool = typer.Option(False, "--offline", help="Force the deterministic reasoner."),
) -> None:
    """Run the closed loop on your own question."""
    scientist = _pick_scientist(force_heuristic=offline)
    loop = ClosedLoop(
        question=question,
        scientist=scientist,
        searcher=get_searcher(settings.mode),
        lab=get_lab(settings.mode, settings.seed),
    )

    console.print(Panel(question, title="Question", border_style="cyan"))

    with console.status("[cyan]gathering evidence...[/cyan]"):
        evidence = loop.gather()
    console.print(f"  retrieved [bold]{len(evidence)}[/bold] pieces of evidence")

    with console.status("[cyan]framing hypotheses...[/cyan]"):
        belief = loop.frame()
    console.print(_belief_table(belief.labelled(), "Priors"))
    console.print(f"  prior entropy: [bold]{belief.entropy:.3f} bits[/bold]\n")

    for i in range(steps):
        with console.status(f"[cyan]step {i + 1}: designing and scoring...[/cyan]"):
            winner, scored = loop.propose(n=candidates)

        table = Table(title=f"Step {i + 1} — candidates scored by information gain",
                      title_justify="left")
        table.add_column("Experiment", overflow="fold")
        table.add_column("EIG", justify="right", width=7)
        table.add_column("Cost", justify="right", width=6)
        table.add_column("Ran", justify="right", width=5)
        table.add_column("Utility", justify="right", width=8)
        for s in scored:
            mark = " [green]<-- chosen[/green]" if s.experiment.id == winner.experiment.id else ""
            table.add_row(
                s.experiment.title + mark,
                f"{s.eig:.3f}",
                f"{s.experiment.cost:.1f}",
                f"{s.times_run}x" if s.times_run else "—",
                f"{s.utility:.3f}",
            )
        console.print(table)

        observation = loop.observe(winner.experiment)
        record = loop.revise(winner.experiment, observation)
        record.step, record.winner = i, winner
        record.decision.expected_information_gain = winner.eig
        record.decision.utility = winner.utility
        record.decision.reasoning = winner.explain()
        loop.history.append(record)

        console.print(
            f"  observed [bold]{observation.outcome_label}[/bold] "
            f"| surprise [bold]{record.surprise_bits:.2f} bits[/bold] "
            f"| entropy {record.entropy_before:.3f} -> [bold]{record.entropy_after:.3f}[/bold]\n"
        )

    # Terminal proposal + summary
    final_winner, _ = loop.propose(n=candidates)
    loop.ledger.append(
        "next_experiment_proposed",
        {
            "title": final_winner.experiment.title,
            "protocol": final_winner.experiment.protocol,
            "eig_bits": round(final_winner.eig, 4),
            "rationale": final_winner.explain(),
        },
        note="terminal proposal (not executed)",
    )

    assert loop.belief is not None
    console.print(_belief_table(loop.belief.labelled(), "Posterior"))
    console.print(
        Panel(
            f"[bold]{final_winner.experiment.title}[/bold]\n{final_winner.experiment.protocol}\n\n"
            f"[dim]{final_winner.explain()}[/dim]",
            title="What it would do next",
            border_style="green",
        )
    )

    from probception.types import RunSummary

    summary = RunSummary(
        run_id=loop.run_id,
        question=question,
        steps=len(loop.history),
        final_belief=loop.belief.labelled(),
        leading_hypothesis=loop.belief.leader().statement,
        entropy_start=loop._entropy_start,
        entropy_end=loop.belief.entropy,
        next_experiment=final_winner.experiment.title,
        ledger_path=str(loop.ledger.path),
    )
    loop.ledger.append("run_finished", summary, note="loop end")

    report = write_report(loop.run_id, loop.run_root)
    console.print(
        f"\nresolved [bold]{summary.entropy_start - summary.entropy_end:.3f} bits[/bold] "
        f"of uncertainty over {summary.steps} experiments"
    )
    console.print(f"ledger:    [cyan]{loop.ledger.path}[/cyan]")
    console.print(f"inspector: [cyan]{report}[/cyan]  (open this in a browser)")
    console.print(f"run id:    [bold]{loop.run_id}[/bold]")


@app.command("risk-profile")
def risk_profile(
    asset: str = typer.Argument(..., help="Clinical asset, e.g. 'VERVE-102 PCSK9 GalNAc-LNP'."),
    trial_design: str = typer.Argument(
        ..., help="Planned trial design: population, phase, dose plan, endpoints."
    ),
    output_json: bool = typer.Option(False, "--json", help="Print the full JSON profile."),
) -> None:
    """Score an in vivo CRISPR clinical asset for safety, efficacy, and success risk."""
    profile = score_asset(asset, trial_design)
    report = write_risk_report(profile, settings.run_dir)

    table = Table(title="Clinical Asset Risk Profile", title_justify="left")
    table.add_column("Metric")
    table.add_column("Score", justify="right")
    table.add_column("Interpretation", overflow="fold")
    table.add_row("Success", f"{profile.success_score:.1f}", profile.status)
    table.add_row("Risk", f"{profile.risk_score:.1f}", "lower is better")
    table.add_row("Safety", f"{profile.safety_score:.1f}", "cell/animal/human weighted")
    table.add_row("Efficacy", f"{profile.efficacy_score:.1f}", "cell/animal/human weighted")
    table.add_row("Confidence", f"{profile.confidence:.2f}", "evidence maturity")
    table.add_row("FDA approval", f"{profile.fda_approval_score:.1f}", "proxy score")
    table.add_row("Commercial", f"{profile.commercial_success_score:.1f}", "proxy score")
    console.print(table)

    console.print(
        Panel(
            "\n".join(profile.reasoning + ["", "Next data:", *profile.next_data_to_collect[:3]]),
            title=f"Reasoning: {profile.generated_from}",
            border_style="cyan",
        )
    )
    console.print(f"report: [cyan]{report}[/cyan]")
    console.print(f"json:   [cyan]{report.with_name('risk_profile.json')}[/cyan]")
    if output_json:
        console.print_json(profile.model_dump_json())


@app.command()
def counterfactual(
    question: str = typer.Option(DEFAULT_QUESTION, help="Question to test."),
    steps: int = typer.Option(3, help="Experiments per world."),
    offline: bool = typer.Option(True, "--offline/--llm", help="Reasoner to use."),
) -> None:
    """Run the same agent against contradictory results and diff what it proposes.

    This is the closing-the-loop proof. If the agent proposes the same next
    experiment no matter what the data said, it fails here — loudly.
    """
    console.print(
        Panel(
            "Running the identical agent against two worlds whose experiments\n"
            "return opposite results, then diffing its next proposal.",
            title="Counterfactual replay",
            border_style="cyan",
        )
    )

    result = run_counterfactual(
        question=question,
        worlds=[
            World("confirming", ["positive"] * steps),
            World("refuting", ["negative"] * steps),
        ],
        scientist=_pick_scientist(force_heuristic=offline),
        steps=steps,
        run_root=str(settings.run_dir),
    )

    table = Table(title="Same agent, different worlds", title_justify="left")
    table.add_column("World")
    table.add_column("Leading hypothesis after evidence", overflow="fold")
    table.add_column("Proposes next", overflow="fold")
    for name in result.proposals:
        table.add_row(name, result.leaders[name], result.proposals[name] or "—")
    console.print(table)

    style = "green" if result.responsive else "red"
    console.print(Panel(result.verdict(), border_style=style))
    for note in result.notes:
        console.print(f"[yellow]note:[/yellow] {note}")

    if not result.responsive:
        raise typer.Exit(code=1)


@app.command()
def score(run_id: str = typer.Argument(..., help="Run id to grade.")) -> None:
    """Grade a finished run's calibration from its ledger alone."""
    ledger = Ledger.load(run_id, str(settings.run_dir))
    if not ledger.read():
        console.print(f"[red]No ledger found for run {run_id}[/red]")
        raise typer.Exit(code=1)
    report = score_run(ledger)
    console.print(Panel(report.summary(), title=f"Calibration — {run_id}", border_style="cyan"))
    if report.n and not report.beats_baseline:
        console.print(
            "[yellow]The agent's probabilities are not beating an uninformed guess. "
            "That is a real finding — report it rather than tuning until it goes away.[/yellow]"
        )


@app.command()
def report(run_id: str = typer.Argument(..., help="Run id to render.")) -> None:
    """Rebuild the standalone HTML inspector for a run."""
    path = write_report(run_id, str(settings.run_dir))
    console.print(f"wrote [cyan]{path}[/cyan]")


@app.command()
def verify(run_id: str = typer.Argument(..., help="Run id to verify.")) -> None:
    """Re-walk a ledger's hash chain to prove it was not edited after the fact."""
    ledger = Ledger.load(run_id, str(settings.run_dir))
    ok, message = ledger.verify()
    console.print(
        Panel(message, title="Ledger integrity", border_style="green" if ok else "red")
    )
    if not ok:
        raise typer.Exit(code=1)


@app.command()
def runs() -> None:
    """List runs on this machine."""
    root = Path(settings.run_dir)
    if not root.exists():
        console.print("no runs yet — try [bold]probception demo[/bold]")
        return
    table = Table(title="Runs", title_justify="left")
    table.add_column("Run id")
    table.add_column("Entries", justify="right")
    table.add_column("Report")
    for d in sorted(root.iterdir()):
        if (d / "ledger.jsonl").exists():
            n = len(Ledger.load(d.name, str(root)).read())
            table.add_row(d.name, str(n), "yes" if (d / "report.html").exists() else "—")
    console.print(table)


if __name__ == "__main__":
    app()
