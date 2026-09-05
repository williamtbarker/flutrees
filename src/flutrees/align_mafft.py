from __future__ import annotations
import os
import subprocess
from pathlib import Path

def mafft_align(input_fasta: Path, output_fasta: Path, mafft: str, threads: int) -> None:
    slurm_tmp = os.environ.get("SLURM_TMPDIR")
    if slurm_tmp and "MAFFT_TMPDIR" not in os.environ:
        os.environ["MAFFT_TMPDIR"] = slurm_tmp

    cmd = [mafft, "--auto", "--thread", str(threads), str(input_fasta)]
    with output_fasta.open("w", encoding="utf-8") as out:
        subprocess.run(cmd, stdout=out, stderr=subprocess.PIPE, text=True, check=True)
