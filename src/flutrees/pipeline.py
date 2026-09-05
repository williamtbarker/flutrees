from __future__ import annotations

import os
from pathlib import Path
from typing import List

import pandas as pd
from Bio import SeqIO

from .config import RunConfig
from .io_fasta import load_fasta_extract_all
from .align_mafft import mafft_align
from .mutations import choose_mode_reference, call_mutations, mutation_counts
from .tree_build import build_tree, prune_tree
from .exports import write_tables, write_tree, write_node_summary, write_summary, write_pdf

def _threads(cfg: RunConfig) -> int:
    return cfg.resolved_threads()

def run_many(cfg: RunConfig, inputs: List[Path], outdir: Path, run_id: str) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    run_root = outdir / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    for fasta in inputs:
        run_one(cfg, fasta, run_root)

def run_one(cfg: RunConfig, fasta: Path, run_root: Path) -> None:
    base_raw = fasta.stem
    base = base_raw.replace(" ", "_")
    out = run_root / base
    out.mkdir(parents=True, exist_ok=True)

    loaded = load_fasta_extract_all(fasta, cfg.start_residue, cfg.end_residue)
    metadata_df: pd.DataFrame = loaded["metadata_df"]

    extracted_fa = out / "extracted.fasta"
    SeqIO.write(loaded["extracted_records"], str(extracted_fa), "fasta")

    aligned_fa = out / "aligned.fasta"
    mafft_align(extracted_fa, aligned_fa, cfg.mafft, _threads(cfg))

    ref_id, ref_seq = choose_mode_reference(aligned_fa)
    mutation_df = call_mutations(aligned_fa, ref_seq, cfg.start_residue)
    mut_counts = mutation_counts(mutation_df)

    tree_full = build_tree(mutation_df, cfg.max_depth, cfg.min_split, cfg.min_freq)
    tree_pruned = prune_tree(tree_full, cfg.prune_cutoff)

    write_tables(out, metadata_df, mutation_df, mut_counts)
    write_tree(out / "tree_full.json", tree_full)
    write_tree(out / "tree_pruned.json", tree_pruned)
    write_node_summary(out / "node_summary.tsv", tree_full, tree_pruned)

    summary = {
        "input_name": fasta.name,
        "input_path": str(fasta),
        "n_records": int(loaded["n_records"]),
        "start_residue": cfg.start_residue,
        "end_residue": cfg.end_residue,
        "reference_id": ref_id,
        "top_mutations": mut_counts.head(25).to_dict(orient="records"),
        "config": {
            "max_depth": cfg.max_depth,
            "min_split": cfg.min_split,
            "min_freq": cfg.min_freq,
            "prune_cutoff": cfg.prune_cutoff,
        }
    }
    write_summary(out / "summary.json", summary)
    write_pdf(out / "report.pdf", summary, mut_counts, tree_pruned)

    # keep extracted/aligned by default for population-level traceability
    (out / "run_info.txt").write_text(
        f"JOB={os.environ.get('SLURM_JOB_ID','')}\nTASK={os.environ.get('SLURM_ARRAY_TASK_ID','')}\n",
        encoding="utf-8"
    )
