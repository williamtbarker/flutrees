from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Tuple, Dict, List

import pandas as pd
from Bio import SeqIO


def choose_mode_reference(aligned_fasta: Path) -> Tuple[str, str]:
    """
    Returns (reference_record_id, reference_sequence_string) where the ref sequence is the most common
    aligned sequence string across ALL records (no dedup).
    """
    counter: Counter[str] = Counter()
    first_id_for_seq: Dict[str, str] = {}

    for rec in SeqIO.parse(str(aligned_fasta), "fasta"):
        s = str(rec.seq)
        counter[s] += 1
        if s not in first_id_for_seq:
            first_id_for_seq[s] = rec.id

    if not counter:
        raise ValueError(f"No aligned sequences in {aligned_fasta}")

    ref_seq, _ = counter.most_common(1)[0]
    ref_id = first_id_for_seq[ref_seq]
    return ref_id, ref_seq


def call_mutations(aligned_fasta: Path, ref_seq: str, start_residue: int) -> pd.DataFrame:
    """Reference-residue coordinates; gaps do not advance the reference position.

    Unknown/deleted residues are recorded separately, never interpreted as absence.
    Reference-gap columns (insertions) are outside this substitution-only analysis.
    """
    if not ref_seq or not set(ref_seq) - {"-"}:
        raise ValueError("The selected reference has no residues.")
    rows = []
    for rec in SeqIO.parse(str(aligned_fasta), "fasta"):
        muts: List[str] = []
        uncertain: List[int] = []
        s = str(rec.seq)
        if len(s) != len(ref_seq):
            raise ValueError(f"Alignment length mismatch for {rec.id}.")
        pos = start_residue - 1
        for ra, aa in zip(ref_seq, s):
            if ra == "-":
                continue
            pos += 1
            if ra not in "ACDEFGHIKLMNPQRSTVWY" or aa not in "ACDEFGHIKLMNPQRSTVWY":
                uncertain.append(pos)
            elif ra != aa:
                muts.append(f"{ra}{pos}{aa}")
        rows.append({"record_id": rec.id, "mutations": muts, "uncertain_positions": uncertain})
    if not rows:
        raise ValueError("The alignment is empty.")
    return pd.DataFrame(rows)


def mutation_counts(mutation_df: pd.DataFrame) -> pd.DataFrame:
    mc = (
        mutation_df.explode("mutations")
        .dropna(subset=["mutations"])
        .groupby("mutations", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
    )
    return mc
