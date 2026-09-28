"""Analysis orchestration with explicit completion and failure records."""

import hashlib
import html
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from Bio import SeqIO

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
    except Exception as error:
        write_summary(
            root / "status.json",
            {"status": "failed", "error": str(error), "completed_datasets": len(links)},
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
        )
        if not all((out / name).is_file() and (out / name).stat().st_size > 0 for name in required):
            raise ValueError(f"An output is missing or empty. Results are incomplete: {out}")
    except Exception as error:
        write_summary(out / "status.json", {"status": "failed", "error": str(error)})
        raise
    artifacts = {p.name: p.stat().st_size for p in out.iterdir() if p.name != "status.json"}
    write_summary(
        out / "status.json", {"status": "complete", "artifacts": artifacts, "version": __version__}
    )
    return out


def _analyze(cfg, fasta, out, progress):
    progress("Reading protein sequences and checking the residue window...")
    loaded = load_fasta_extract_all(fasta, cfg.start_residue, cfg.end_residue)
    metadata = loaded["metadata_df"]
    extracted = out / "extracted.fasta"
    SeqIO.write(loaded["extracted_records"], str(extracted), "fasta")
    aligned = out / "aligned.fasta"
    progress("Aligning sequences with MAFFT. Large datasets may take several minutes...")
    mafft_align(extracted, aligned, cfg.mafft, cfg.resolved_threads())
    aligned_ids = [r.id for r in SeqIO.parse(str(aligned), "fasta")]
    if sorted(aligned_ids) != sorted(metadata.record_id.tolist()):
        raise ValueError("MAFFT output IDs do not match the input records.")
    ref_id, ref_seq = choose_mode_reference(aligned)
    mutations = call_mutations(aligned, ref_seq, cfg.start_residue)
    counts = mutation_counts(mutations)
    counts["fraction_of_input"] = counts["count"] / loaded["n_records"]
    full = build_tree(mutations, cfg.max_depth, cfg.min_split, cfg.min_freq)
    pruned = prune_tree(full, cfg.prune_cutoff)
    warnings = []
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
        "input_sha256": hashlib.sha256(fasta.read_bytes()).hexdigest(),
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
