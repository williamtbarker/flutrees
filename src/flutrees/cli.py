"""Backward-compatible command line plus example and desktop entry points."""

import os
import webbrowser
from importlib.resources import files
from pathlib import Path
from typing import List, Optional

import typer
from xlsxwriter.exceptions import FileCreateError
from . import __version__
from .config import RunConfig

app = typer.Typer(
    add_completion=False,
    help="FluTrees: protein FASTA to visual trees, PDF reports, and Excel tables.",
)


def show_version(value: bool):
    if value:
        typer.echo(f"FluTrees {__version__}")
        raise typer.Exit()


def demo_path():
    return Path(str(files("flutrees").joinpath("data/example.fasta")))


@app.command()
def run(
    inputs: Optional[List[Path]] = typer.Option(
        None,
        "-i",
        "--input",
        exists=True,
        readable=True,
        dir_okay=False,
        help="Protein FASTA file. Repeat -i for multiple files.",
    ),
    outdir: Path = typer.Option(Path("runs"), "-o", "--outdir", help="Results folder"),
    run_id: Optional[str] = typer.Option(
        None, "--run-id", help="Run folder name; existing runs are never overwritten"
    ),
    mafft: str = typer.Option("mafft", "--mafft", help="MAFFT executable in PATH or its full path"),
    threads: Optional[int] = typer.Option(
        None, "--threads", help="CPU threads; default: SLURM setting or 8"
    ),
    start_residue: int = typer.Option(
        84, "--start", help="First input residue (1-based, inclusive)"
    ),
    end_residue: int = typer.Option(284, "--end", help="Last input residue (inclusive)"),
    max_depth: int = typer.Option(10, "--max-depth", help="Maximum tree depth, 0–20; 0 keeps only the root"),
    min_split: int = typer.Option(5, "--min-split", help="Minimum records in each child group"),
    min_freq: float = typer.Option(0.05, "--min-freq", help="Minimum fraction of the current node in each child, 0–0.5; 0.05 = 5%"),
    prune_cutoff: int = typer.Option(
        10, "--prune-cutoff", help="Hide groups smaller than this in simplified view"
    ),
    tree_mode: str = typer.Option(
        "frequency", "--tree-mode", help="Tree view: frequency (legacy), balanced, diversity, or all. Aligns once."
    ),
    reference: Optional[str] = typer.Option(
        None, "--reference", help="Use auto for the modal reference; do not combine with --reference-id."
    ),
    reference_id: Optional[str] = typer.Option(
        None, "--reference-id", help="Use exactly one matching original FASTA ID; default is the modal sequence."
    ),
    reproducible: Optional[bool] = typer.Option(
        None, "--reproducible/--legacy-alignment", help="Alignment flags: frequency alone defaults to legacy; other views default to reproducible. Override either default explicitly."
    ),
    demo: bool = typer.Option(False, "--demo", help="Run the included synthetic protein example"),
    figure_width: float = typer.Option(14.0, "--figure-width", help="Tree figure width in inches, 6–30; width/height sets aspect ratio"),
    figure_height: float = typer.Option(8.5, "--figure-height", help="Tree figure height in inches, 4–24"),
    level_spacing: float = typer.Option(1.0, "--level-spacing", help="Horizontal gap between tree levels, 0.25–4 times the base gap"),
    node_spacing: float = typer.Option(1.0, "--node-spacing", help="Vertical gap between tree nodes, 0.25–4 times the base gap"),
    line_width: float = typer.Option(1.5, "--line-width", help="Branch stroke width in points, 0.25–5"),
    open_results: bool = typer.Option(
        False, "--open", help="Open the results overview in your browser"
    ),
    gui: bool = typer.Option(False, "--gui", help="Open the desktop file-selection window"),
    version: Optional[bool] = typer.Option(
        None, "--version", callback=show_version, is_eager=True, help="Show installed version"
    ),
):
    if gui:
        from .gui import launch

        launch()
        return
    if demo and inputs:
        raise typer.BadParameter("Use --demo by itself, or select your own files with -i.")
    if demo:
        inputs = [demo_path()]
    if not inputs:
        typer.echo(
            "Choose protein FASTA files with -i, try --demo --open, or use --gui for file selection."
        )
        raise typer.Exit(2)
    try:
        if reference not in {None, "auto"}:
            raise ValueError("Reference selection must be auto, or use --reference-id with an original FASTA ID.")
        if reference == "auto" and reference_id is not None:
            raise ValueError("Use --reference auto or --reference-id, not both.")
        cfg = RunConfig(
            mafft, threads, start_residue, end_residue, max_depth, min_split, min_freq, prune_cutoff,
            tree_mode=tree_mode, reference_id=reference_id, reproducible=reproducible,
            figure_width=figure_width, figure_height=figure_height,
            level_spacing=level_spacing, node_spacing=node_spacing, line_width=line_width,
        )
        if run_id is None:
            sj = os.environ.get("SLURM_JOB_ID")
            run_id = f"job{sj}" if sj else RunConfig.default_run_id()
        from .pipeline import run_many

        root = run_many(cfg, inputs, outdir.resolve(), run_id, typer.echo)
    except (ValueError, OSError, FileCreateError) as error:
        typer.echo(f"Could not complete analysis: {error}", err=True)
        raise typer.Exit(1) from error
    if open_results and not webbrowser.open((root / "START_HERE.html").as_uri()):
        typer.echo(
            "Your browser did not open automatically. Open START_HERE.html at the path shown above."
        )
