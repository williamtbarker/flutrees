from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from .metadata import parse_header_robust

AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")


def extract_region(seq: Seq, start_residue: int, end_residue: int) -> Seq:
    if start_residue < 1 or end_residue < start_residue:
        raise ValueError("Invalid residue window: require 1 <= start <= end.")
    start_i = start_residue - 1
    end_i = end_residue
    expected = end_residue - start_residue + 1

    if len(seq) >= end_i:
        out = seq[start_i:end_i]
    elif len(seq) > start_i:
        out = seq[start_i:]
        out = out + Seq("-" * (expected - len(out)))
    else:
        out = Seq("-" * expected)

    return out


def load_fasta_extract_all(fasta: Path, start_residue: int, end_residue: int) -> Dict[str, Any]:
    records = list(SeqIO.parse(str(fasta), "fasta"))
    if not records:
        raise ValueError(f"No FASTA records found: {fasta}")

    seen = set()
    meta_rows: List[dict] = []
    extracted: List[SeqRecord] = []

    for r in records:
        sequence = str(r.seq).upper()
        if not r.id:
            raise ValueError("Every FASTA record needs a nonempty ID after >.")
        if not sequence or set(sequence) - set("ACDEFGHIKLMNPQRSTVWYXBZJUO*?-"):
            raise ValueError(f"Invalid protein sequence in record {r.id}.")
        if "-" in sequence:
            raise ValueError(
                f"Record {r.id} contains alignment gaps. Supply unaligned protein FASTA; "
                "window positions count residues, not alignment columns."
            )
        terminal_stop_removed = sequence.endswith("*")
        if terminal_stop_removed:
            sequence = sequence[:-1]
        if "*" in sequence:
            raise ValueError(f"Record {r.id} contains an internal stop (*). Check the protein translation.")
        # MAFFT drops '?' and rejects U/O in amino-acid mode. Preserve positions
        # as unknown observations instead of losing residues or changing numbering.
        normalized_residues = sum(sequence.count(c) for c in "?UO")
        sequence = sequence.translate(str.maketrans("?UO", "XXX"))
        sid = r.id
        if sid in seen:
            k = 2
            while f"{sid}_{k}" in seen:
                k += 1
            sid = f"{sid}_{k}"
        seen.add(sid)

        meta = parse_header_robust(r.description)
        region = extract_region(Seq(sequence), start_residue, end_residue)
        if not set(str(region)) & AMINO_ACIDS:
            raise ValueError(
                f"Record {sid} has no residues that can be interpreted in the selected window. "
                "Check --start, --end, and unknown residues."
            )

        meta_rows.append(
            {
                "record_id": sid,
                **meta,
                "original_id": r.id,
                "input_length": len(sequence),
                "padded_residues": max(0, end_residue - len(sequence)),
                "renamed_duplicate": sid != r.id,
                "normalized_residues": normalized_residues,
                "terminal_stop_removed": terminal_stop_removed,
            }
        )
        extracted.append(SeqRecord(region, id=sid, description=sid))

    metadata_df = pd.DataFrame(meta_rows)

    return {
        "n_records": len(records),
        "metadata_df": metadata_df,
        "extracted_records": extracted,
    }
