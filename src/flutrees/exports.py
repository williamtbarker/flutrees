from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from .tree_build import Node, to_dict, iter_nodes

def write_tables(outdir: Path, metadata_df: pd.DataFrame, mutation_df: pd.DataFrame, mut_counts: pd.DataFrame) -> None:
    metadata_df.to_csv(outdir / "metadata.tsv", sep="\t", index=False)
    # mutations as semicolon-joined for readability
    m = mutation_df.copy()
    m["mutations"] = m["mutations"].apply(lambda x: ";".join(x) if isinstance(x, list) else "")
    m.to_csv(outdir / "mutations_per_record.tsv", sep="\t", index=False)
    mut_counts.to_csv(outdir / "mutation_counts.tsv", sep="\t", index=False)

def write_tree(outpath: Path, tree: Node) -> None:
    outpath.write_text(json.dumps(to_dict(tree), indent=2), encoding="utf-8")

def write_node_summary(outpath: Path, tree_full: Node, tree_pruned: Node) -> None:
    rows = []
    for tag, t in [("full", tree_full), ("pruned", tree_pruned)]:
        for n in iter_nodes(t):
            rows.append({"view": tag, "node_id": n.node_id, "depth": n.depth, "label": n.label, "support": n.support})
    pd.DataFrame(rows).to_csv(outpath, sep="\t", index=False)

def write_summary(outpath: Path, summary: Dict[str, Any]) -> None:
    outpath.write_text(json.dumps(summary, indent=2), encoding="utf-8")

def write_pdf(pdf_path: Path, summary: Dict[str, Any], mut_counts: pd.DataFrame, tree_pruned: Node) -> None:
    with PdfPages(pdf_path) as pdf:
        # Summary page
        fig = plt.figure(figsize=(8.5, 11))
        plt.axis("off")
        lines = [
            f"Input: {summary['input_name']}",
            f"Records: {summary['n_records']}",
            f"Residues: {summary['start_residue']}-{summary['end_residue']}",
            f"Reference: {summary['reference_id']}",
            "",
            "Top mutations:",
        ]
        for row in summary["top_mutations"]:
            lines.append(f"  {row['mutations']}: {row['count']}")
        plt.text(0.05, 0.95, "\n".join(lines), va="top", family="monospace", fontsize=10)
        pdf.savefig(fig); plt.close(fig)

        # Top mutations bar plot
        top = mut_counts.head(25)
        fig = plt.figure(figsize=(11, 8.5))
        plt.bar(range(len(top)), top["count"])
        plt.xticks(range(len(top)), top["mutations"], rotation=90, fontsize=7)
        plt.ylabel("Count")
        plt.title("Top 25 mutations")
        plt.tight_layout()
        pdf.savefig(fig); plt.close(fig)

        # Pruned tree text view (scales)
        def lines_tree(n: Node, indent: int = 0):
            yield " " * indent + f"[{n.node_id}] {n.label} (support={n.support})"
            if n.left: yield from lines_tree(n.left, indent + 2)
            if n.right: yield from lines_tree(n.right, indent + 2)

        tree_lines = list(lines_tree(tree_pruned))
        fig = plt.figure(figsize=(8.5, 11))
        plt.axis("off")
        plt.title("Pruned mutation decision tree", fontsize=12)
        plt.text(0.05, 0.95, "\n".join(tree_lines[:2500]), va="top", family="monospace", fontsize=7)
        pdf.savefig(fig); plt.close(fig)
