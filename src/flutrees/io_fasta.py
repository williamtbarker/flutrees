from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from .metadata import parse_header_robust


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
        if not r.seq or set(str(r.seq).upper()) - set("ACDEFGHIKLMNPQRSTVWYXBZJUO*?-"):
            raise ValueError(f"Invalid protein sequence in record {r.id}.")
        sid = r.id
        if sid in seen:
            k = 2
            while f"{sid}_{k}" in seen:
                k += 1
            sid = f"{sid}_{k}"
        seen.add(sid)

        meta = parse_header_robust(r.description)
        region = extract_region(r.seq.upper(), start_residue, end_residue)
        if not set(str(region)) - {"-"}:
            raise ValueError(
                f"Record {sid} has no residues in the selected window. Check --start and --end."
            )

        meta_rows.append(
            {
                "record_id": sid,
                **meta,
                "original_id": r.id,
                "input_length": len(r.seq),
                "padded_residues": max(0, end_residue - len(r.seq)),
                "renamed_duplicate": sid != r.id,
            }
        )
        extracted.append(SeqRecord(region, id=sid, description=sid))

    metadata_df = pd.DataFrame(meta_rows)

    return {
        "n_records": len(records),
        "metadata_df": metadata_df,
        "extracted_records": extracted,
    }
