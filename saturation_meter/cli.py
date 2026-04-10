"""
saturation-meter CLI

Commands
--------
  analyze   Full saturation report (rich terminal output or --json-output)
  curve     Saturation curve data as JSON (pipe-friendly for plotting)
"""

import json
import sys
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .core import analyze_saturation
from .io import load_file, report_to_dict
from .models import SaturationReport

console = Console()


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


@click.group()
@click.version_option()
def cli() -> None:
    """saturation-meter — thematic saturation estimation for qualitative research."""


# ---------------------------------------------------------------------------
# analyze command
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--threshold",
    default=0.05,
    show_default=True,
    help="New-theme rate (0–1) below which an interview is non-contributory.",
)
@click.option(
    "--window",
    default=3,
    show_default=True,
    help="Consecutive sub-threshold interviews required to signal saturation.",
)
@click.option("--json-output", is_flag=True, help="Emit results as JSON instead of rich output.")
@click.option(
    "--llm-backend",
    type=click.Choice(["openai", "anthropic", "gemini"]),
    default=None,
    help="LLM backend for narrative enrichment (community scaffolding — optional).",
)
def analyze(
    input_file: Path,
    threshold: float,
    window: int,
    json_output: bool,
    llm_backend: str | None,
) -> None:
    """Analyze thematic saturation from a coded transcript dataset."""

    try:
        interviews = load_file(input_file)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)

    if not interviews:
        console.print("[red]No interview records found in the file.[/red]")
        sys.exit(1)

    report = analyze_saturation(interviews, new_theme_threshold=threshold, window_size=window)

    if llm_backend:
        try:
            from .llm import enrich_with_narrative  # noqa: PLC0415

            report = enrich_with_narrative(report, backend=llm_backend)
        except NotImplementedError as exc:
            console.print(f"[yellow]LLM enrichment unavailable: {exc}[/yellow]")
        except ImportError as exc:
            console.print(f"[yellow]LLM enrichment unavailable: {exc}[/yellow]")

    if json_output:
        click.echo(json.dumps(report_to_dict(report), indent=2))
        return

    _render_report(report)


# ---------------------------------------------------------------------------
# curve command
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("--threshold", default=0.05, show_default=True)
@click.option("--window", default=3, show_default=True)
def curve(input_file: Path, threshold: float, window: int) -> None:
    """Output the saturation curve as JSON (suitable for plotting)."""

    try:
        interviews = load_file(input_file)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)

    report = analyze_saturation(interviews, new_theme_threshold=threshold, window_size=window)

    curve_data = [
        {
            "interview_index": p.interview_index,
            "participant_id": p.participant_id,
            "new_themes": p.new_themes_count,
            "cumulative_themes": p.cumulative_themes_count,
            "new_theme_rate": p.new_theme_rate,
            "marginal_discovery_rate": p.marginal_discovery_rate,
        }
        for p in report.points
    ]
    click.echo(json.dumps(curve_data, indent=2))


# ---------------------------------------------------------------------------
# Rich renderer
# ---------------------------------------------------------------------------


def _render_report(report: SaturationReport) -> None:
    status_text = "SATURATED" if report.is_saturated else "NOT YET SATURATED"
    border = "green" if report.is_saturated else "yellow"

    console.print()
    console.print(
        Panel.fit(
            f"[bold]{status_text}[/bold]  ·  confidence: [bold]{report.confidence}[/bold]",
            title="[bold]saturation-meter[/bold]",
            border_style=border,
        )
    )

    console.print(f"\n  Interviews analysed : [bold]{report.total_interviews}[/bold]")
    console.print(f"  Unique themes found : [bold]{report.total_unique_themes}[/bold]")
    if report.is_saturated:
        console.print(
            f"  Saturation from     : interview [bold]{report.estimated_saturation_index}[/bold]"
            f"  (participant [bold]{report.estimated_saturation_participant}[/bold])"
        )
    console.print()

    # Saturation curve table
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim", padding=(0, 1))
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Participant", width=14)
    table.add_column("New themes", width=11, justify="right")
    table.add_column("Cumulative", width=11, justify="right")
    table.add_column("Rate", width=7, justify="right")
    table.add_column("Signal", width=12)

    for p in report.points:
        rate_str = f"{p.new_theme_rate * 100:.1f}%"

        if report.estimated_saturation_index and p.interview_index >= report.estimated_saturation_index:
            signal = "[green]● saturated[/green]"
        elif p.new_theme_rate > 0.25:
            signal = "[bright_yellow]○ active[/bright_yellow]"
        elif p.new_theme_rate > 0.10:
            signal = "[dim]○ slowing[/dim]"
        else:
            signal = "[dim]–[/dim]"

        table.add_row(
            str(p.interview_index),
            p.participant_id,
            str(p.new_themes_count),
            str(p.cumulative_themes_count),
            rate_str,
            signal,
        )

    console.print(table)

    # Stop-point panel
    console.print(
        Panel(
            report.stop_recommendation,
            title="[bold]Stop-point recommendation[/bold]",
            border_style="blue",
            padding=(0, 1),
        )
    )

    # Warnings
    if report.warnings:
        console.print()
        for w in report.warnings:
            console.print(f"  [yellow]⚠[/yellow]  {w}")

    # Narrative (LLM-generated)
    if report.narrative:
        console.print()
        console.print(
            Panel(
                report.narrative,
                title="[bold]Narrative (LLM-generated)[/bold]",
                border_style="dim",
                padding=(0, 1),
            )
        )

    console.print()
