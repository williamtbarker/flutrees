"""Analysis orchestration with explicit completion and failure records."""

import hashlib
import html
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from Bio import SeqIO
from Bio.SeqRecord import SeqRecord

from . import __version__
from .config import RunConfig
from .io_fasta import load_fasta_extract_all
from .align_mafft import mafft_align, check_mafft
from .mutations import choose_mode_reference, call_mutations, mutation_counts
from .tree_build import build_tree, prune_tree, iter_nodes
from .figures import write_tree_figures
from .exports import (
    STYLE,
    write_tables,
    write_tree,
    write_node_summary,
    write_summary,
    write_pdf,
    write_workbook,
    write_html,
)


def input_name(path):
    name = path.stem.replace(" ", "_")
    if name in {"", ".", ".."}:
        raise ValueError("Input filename must have a usable name before its extension.")
    return name


def run_many(cfg, inputs, outdir, run_id, progress=print):
    if not inputs:
        raise ValueError("Choose at least one protein FASTA file.")
    if not run_id or run_id in {".", ".."} or any(c in run_id for c in "/\\:"):
        raise ValueError("Run ID must be a folder name, without path separators or colons.")
    names = [input_name(p) for p in inputs]
    if len({n.casefold() for n in names}) != len(names):
        raise ValueError(
            "Input filenames would share an output folder. Give each FASTA file a distinct name."
        )
    check_mafft(cfg.mafft)
    # Preflight every input before making any output folder.
    for fasta in inputs:
        load_fasta_extract_all(fasta, cfg.start_residue, cfg.end_residue)
    root = outdir / run_id
    root.mkdir(parents=True, exist_ok=False)
    links = []
    write_summary(root / "status.json", {"status": "running", "datasets": names})
    try:
        for i, fasta in enumerate(inputs, 1):
            progress(f"[{i}/{len(inputs)}] {fasta.name}")
            result = run_one(cfg, fasta, root, progress)
            links.append(
                f'<li><a href="{quote(result.name)}/START_HERE.html">{html.escape(fasta.name)}</a></li>'
            )
        index = f'<!doctype html><html lang="en"><meta charset="utf-8"><title>FluTrees results</title><style>{STYLE}</style><body><h1>Analysis complete</h1><p>Choose a dataset to open its report, Excel workbook, and visual trees.</p><ul>{"".join(links)}</ul></body></html>'
        (root / "START_HERE.html").write_text(index, encoding="utf-8")
        write_summary(
            root / "status.json", {"status": "complete", "datasets": names, "version": __version__}
        )
    except (Exception, KeyboardInterrupt) as error:
        write_summary(
            root / "status.json",
            {"status": "failed", "error": str(error) or "Analysis interrupted.", "completed_datasets": len(links)},
        )
        raise
    progress(f"Complete. Open this file: {root.resolve() / 'START_HERE.html'}")
    return root


def run_one(cfg: RunConfig, fasta: Path, run_root: Path, progress=print):
    out = run_root / input_name(fasta)
    out.mkdir(parents=True, exist_ok=False)
    write_summary(out / "status.json", {"status": "running"})
    try:
        _analyze(cfg, fasta, out, progress)
        required = (
            "report.pdf",
            "results.xlsx",
            "START_HERE.html",
            "tree_full.pdf",
            "tree_pruned.pdf",
            "tree_full.json",
            "tree_pruned.json",
            "summary.json",
            "metadata.tsv",
            "aligned.fasta",
            "input.fasta",
            "extracted.fasta",
            "mafft_input.fasta",
            "mutations_per_record.tsv",
            "mutation_counts.tsv",
            "node_summary.tsv",
            "node_membership.tsv",
            "tree_full.svg",
            "tree_pruned.svg",
            "tree_full.png",
            "tree_pruned.png",
            "run_info.txt",
        )
        if not all((out / name).is_file() and (out / name).stat().st_size > 0 for name in required):
            raise ValueError(f"An output is missing or empty. Results are incomplete: {out}")
    except (Exception, KeyboardInterrupt) as error:
        write_summary(out / "status.json", {"status": "failed", "error": str(error) or "Analysis interrupted."})
        raise
    artifacts = {p.name: p.stat().st_size for p in out.iterdir() if p.name != "status.json"}
    write_summary(
        out / "status.json", {"status": "complete", "artifacts": artifacts, "version": __version__}
    )
    return out


def _analyze(cfg, fasta, out, progress):
    progress("Reading protein sequences and checking the residue window...")
    snapshot = out / "input.fasta"
    input_bytes = fasta.read_bytes()
    snapshot.write_bytes(input_bytes)
    loaded = load_fasta_extract_all(snapshot, cfg.start_residue, cfg.end_residue)
    metadata = loaded["metadata_df"]
    extracted = out / "extracted.fasta"
    SeqIO.write(loaded["extracted_records"], str(extracted), "fasta")
    # Compact transport IDs avoid MAFFT's header-length limit. Restore public
    # record IDs and input order before reference selection or interpretation.
    transport = {
        f"ft_{i:09d}": rec for i, rec in enumerate(loaded["extracted_records"], 1)
    }
    metadata["alignment_id"] = list(transport)
    mafft_input = out / "mafft_input.fasta"
    SeqIO.write(
        [SeqRecord(rec.seq, id=key, description="") for key, rec in transport.items()],
        str(mafft_input), "fasta",
    )
    aligned = out / "aligned.fasta"
    progress("Aligning sequences with MAFFT. Large datasets may take several minutes...")
    mafft_align(mafft_input, aligned, cfg.mafft, cfg.resolved_threads())
    aligned_records = list(SeqIO.parse(str(aligned), "fasta"))
    if sorted(r.id for r in aligned_records) != sorted(transport):
        raise ValueError("MAFFT output IDs do not match the input records.")
    by_id = {rec.id: rec for rec in aligned_records}
    restored = []
    for key, original in transport.items():
        rec = by_id[key]
        if str(rec.seq).replace("-", "") != str(original.seq).replace("-", ""):
            raise ValueError(f"MAFFT changed or removed residues in record {original.id}. Analysis stopped.")
        rec.id = original.id
        rec.description = ""
        restored.append(rec)
    SeqIO.write(restored, str(aligned), "fasta")
    ref_id, ref_seq = choose_mode_reference(aligned)
    mutations = call_mutations(aligned, ref_seq, cfg.start_residue)
    counts = mutation_counts(mutations)
    counts["fraction_of_input"] = counts["count"] / loaded["n_records"]
    full = build_tree(mutations, cfg.max_depth, cfg.min_split, cfg.min_freq)
    pruned = prune_tree(full, cfg.prune_cutoff)
    warnings = []
    if metadata.normalized_residues.sum():
        warnings.append("Input ?, U, and O residues were preserved as X (unknown), without shifting positions. See normalized_residues in Records.")
    if metadata.terminal_stop_removed.any():
        warnings.append("Terminal stop markers (*) were removed before extraction. Internal stops are not accepted.")
    expected_length = cfg.end_residue - cfg.start_residue + 1
    if len(ref_seq.replace("-", "")) < expected_length:
        warnings.append("The selected reference is shorter than the requested window. Reference-gap columns are excluded; some positions cannot be compared.")
    incomplete = sum(bool(x) for x in mutations.uncertain_positions)
    if incomplete:
        warnings.append(
            f"{incomplete} record(s) have missing or ambiguous observations. A split is withheld if any record in that node has an uncertain residue at that position."
        )
    if metadata.padded_residues.sum():
        warnings.append(
            "Some inputs are shorter than the window end; missing tails were padded. See Records in the workbook."
        )
    if metadata.renamed_duplicate.any():
        warnings.append(
            "Duplicate IDs were renamed; original IDs and headers are retained in the workbook."
        )
    hidden = len(list(iter_nodes(full))) - len(list(iter_nodes(pruned)))
    if hidden:
        warnings.append(
            f"Pruning hides {hidden} nodes with fewer than {cfg.prune_cutoff} records. The full tree retains every group."
        )
    if full.left is None:
        warnings.append(full.stop_reason)
    if counts.empty:
        warnings.append(
            "No substitutions were called. Check the reference, selected window, and missing observations before interpreting this as identity."
        )
    if not warnings:
        warnings.append("No missing-residue, duplicate-ID, or pruning warnings were detected.")
    summary = {
        "input_name": fasta.name,
        "input_path": str(fasta.resolve()),
        "n_records": loaded["n_records"],
        "start_residue": cfg.start_residue,
        "end_residue": cfg.end_residue,
        "reference_id": ref_id,
        "reference_sequence": ref_seq,
        "coordinate_system": "ungapped selected reference residues; window start offset",
        "version": __version__,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "top_mutations": counts.head(25).to_dict(orient="records"),
        "config": asdict(cfg),
        "resolved_threads": cfg.resolved_threads(),
        "mafft_executable": check_mafft(cfg.mafft),
        "warnings": warnings,
    }
    progress("Building visual trees, the PDF report, and Excel workbook...")
    write_tables(out, metadata, mutations, counts)
    write_tree(out / "tree_full.json", full)
    write_tree(out / "tree_pruned.json", pruned)
    write_node_summary(out / "node_summary.tsv", full, pruned)
    write_summary(out / "summary.json", summary)
    write_pdf(out / "report.pdf", summary, counts, pruned)
    write_tree_figures(out, full, "tree_full")
    write_tree_figures(out, pruned, "tree_pruned")
    write_workbook(out / "results.xlsx", summary, metadata, mutations, counts, full, pruned)
    write_html(out / "START_HERE.html", summary, full, pruned, metadata)
    (out / "run_info.txt").write_text(
        f"JOB={os.environ.get('SLURM_JOB_ID', '')}\nTASK={os.environ.get('SLURM_ARRAY_TASK_ID', '')}\nVERSION={__version__}\n",
        encoding="utf-8",
    )
