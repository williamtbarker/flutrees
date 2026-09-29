from __future__ import annotations
import os
import subprocess
import shutil
from pathlib import Path


def check_mafft(mafft: str) -> str:
    executable = shutil.which(mafft)
    if not executable:
        raise ValueError(
            "MAFFT was not found. Install MAFFT, or select its executable with --mafft."
        )
    return executable


def mafft_align(input_fasta: Path, output_fasta: Path, mafft: str, threads: int, reproducible: bool = True) -> None:
    executable = check_mafft(mafft)
    env = os.environ.copy()
    slurm_tmp = os.environ.get("SLURM_TMPDIR")
    if slurm_tmp and "MAFFT_TMPDIR" not in env:
        env["MAFFT_TMPDIR"] = slurm_tmp

    cmd = alignment_command(executable, input_fasta, threads, reproducible)
    log = output_fasta.with_name("mafft.log")
    with output_fasta.open("w", encoding="utf-8") as out, log.open("w", encoding="utf-8") as err:
        result = subprocess.run(cmd, stdout=out, stderr=err, text=True, env=env, check=False)
    if result.returncode:
        raise ValueError(f"MAFFT failed (exit {result.returncode}). Details: {log}")


def alignment_command(executable, input_fasta, threads, reproducible=True):
    cmd = [
        executable,
        "--amino",
        "--inputorder",
        "--auto",
        "--thread",
        str(threads),
        str(input_fasta.resolve()),
    ]
    if reproducible:
        cmd[-1:-1] = ["--threadit", "0"]
    return cmd
