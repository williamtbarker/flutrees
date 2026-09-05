from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import typer
from .config import RunConfig

app = typer.Typer(add_completion=False, help="flutrees: mutation decision-tree reporting")

@app.command()
def run(
    inputs: List[Path] = typer.Option(..., "-i", "--input", exists=True, readable=True, help="Input FASTA files"),
    outdir: Path = typer.Option(Path("runs"), "-o", "--outdir", help="Base output directory"),
    run_id: Optional[str] = typer.Option(None, "--run-id", help="Run identifier (default: job<SLURM_JOB_ID> or timestamp)"),
    mafft: str = typer.Option("mafft", "--mafft", help="MAFFT executable in PATH (or absolute path)"),
    threads: Optional[int] = typer.Option(None, "--threads", help="Threads (default: SLURM_CPUS_PER_TASK or 8)"),
    start_residue: int = typer.Option(84, "--start", help="Start residue (1-based, inclusive)"),
    end_residue: int = typer.Option(284, "--end", help="End residue (1-based, inclusive)"),
    max_depth: int = typer.Option(10, "--max-depth", help="Max tree depth"),
    min_split: int = typer.Option(5, "--min-split", help="Minimum sequences per child to split"),
    min_freq: float = typer.Option(0.05, "--min-freq", help="Min mutation frequency (fraction of node sequences)"),
    prune_cutoff: int = typer.Option(10, "--prune-cutoff", help="Hide nodes with < N sequences in pruned tree"),
):
    cfg = RunConfig(
        mafft=mafft,
        threads=threads,
        start_residue=start_residue,
        end_residue=end_residue,
        max_depth=max_depth,
        min_split=min_split,
        min_freq=min_freq,
        prune_cutoff=prune_cutoff,
    )

    if run_id is None:
        sj = os.environ.get("SLURM_JOB_ID")
        run_id = f"job{sj}" if sj else RunConfig.default_run_id()

    # Lazy import to keep `--help` working even if downstream modules are mid-edit
    from .pipeline import run_many

    run_many(cfg, inputs, outdir.resolve(), run_id)
