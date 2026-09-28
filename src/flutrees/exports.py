"""Portable, human-readable results backed by one shared set of tables."""

import html
import json
import textwrap
from pathlib import Path

import pandas as pd
from .figures import tree_figure, tree_pages
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from .tree_build import to_dict

METHOD = (
    "Mutation decision tree, not a phylogeny. Counts represent sequence records, including duplicates. "
    "Reference: most common aligned sequence; ties use first input occurrence. Positions count ungapped "
    "reference residues starting at the selected window start, not standardized HA numbering. "
    "Reference-gap columns are ignored (substitutions only). Splits at positions with missing or ambiguous "
    "observations in that node are withheld. Input sequences must share a consistent numbering convention."
)


def flat_mutations(mutation_df):
    out = mutation_df.copy()
    for col in ("mutations", "uncertain_positions"):
        if col in out:
            out[col] = out[col].map(lambda x: ";".join(map(str, x)) if isinstance(x, list) else "")
    return out


def write_tables(outdir, metadata_df, mutation_df, mut_counts):
    metadata_df.to_csv(outdir / "metadata.tsv", sep="\t", index=False)
    flat_mutations(mutation_df).to_csv(outdir / "mutations_per_record.tsv", sep="\t", index=False)
    mut_counts.to_csv(outdir / "mutation_counts.tsv", sep="\t", index=False)


def write_tree(outpath, tree):
    write_summary(outpath, to_dict(tree))


def node_tables(tree_full, tree_pruned):
    rows, members = [], []
    for tag, tree in (("full", tree_full), ("pruned", tree_pruned)):

        def walk(node, parent_id, path, tag=tag, tree=tree):
            path = path + [node.label]
            rows.append(
                {
                    "view": tag,
                    "node_id": node.node_id,
                    "parent_id": parent_id,
                    "depth": node.depth,
                    "label": node.label,
                    "support": node.support,
                    "fraction_of_input": node.support / tree.support,
                    "path": " > ".join(path),
                    "stop_reason": node.stop_reason,
                }
            )
            members.extend(
                {"view": tag, "node_id": node.node_id, "record_id": rid}
                for rid in sorted(node.seqs)
            )
            for child in (node.left, node.right):
                if child is not None:
                    walk(child, node.node_id, path)

        walk(tree, None, [])
    return pd.DataFrame(rows), pd.DataFrame(members)


def write_node_summary(outpath, tree_full, tree_pruned):
    nodes, members = node_tables(tree_full, tree_pruned)
    nodes.to_csv(outpath, sep="\t", index=False)
    members.to_csv(outpath.with_name("node_membership.tsv"), sep="\t", index=False)


def write_summary(outpath: Path, summary):
    outpath.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def write_workbook(outpath, summary, metadata, mutations, counts, full, pruned):
    nodes, members = node_tables(full, pruned)
    records = metadata.merge(flat_mutations(mutations), on="record_id", validate="one_to_one")
    summary_rows = [
        ("Input", summary["input_name"]),
        ("Sequence records", summary["n_records"]),
        ("Reference", summary["reference_id"]),
        ("Residue window", f"{summary['start_residue']}-{summary['end_residue']}"),
        (
            "How to use",
            "Filter Records by mutation; filter Node Membership by view and node_id to identify a group.",
        ),
        ("Interpretation", METHOD),
    ]
    sheets = {
        "Summary": pd.DataFrame(summary_rows, columns=["Item", "Value"]),
        "Records": records,
        "Mutations": counts,
        "Nodes": nodes,
        "Node Membership": members,
        "QC": pd.DataFrame({"Note": summary["warnings"]}),
        "Parameters": pd.DataFrame(list(summary["config"].items()), columns=["Parameter", "Value"]),
    }
    with pd.ExcelWriter(
        outpath,
        engine="xlsxwriter",
        engine_kwargs={"options": {"strings_to_formulas": False, "strings_to_urls": False}},
    ) as writer:
        wrap = writer.book.add_format({"text_wrap": True, "valign": "top"})
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
            ws = writer.sheets[name]
            ws.freeze_panes(1, 0)
            ws.set_column(0, len(df.columns) - 1, 24)
            if not df.empty:
                ws.add_table(
                    0,
                    0,
                    len(df),
                    len(df.columns) - 1,
                    {
                        "columns": [{"header": c} for c in df.columns],
                        "style": "Table Style Medium 2",
                    },
                )
            if name in {"Summary", "QC"}:
                ws.set_column(len(df.columns) - 1, len(df.columns) - 1, 105, wrap)
                ws.set_default_row(60)
            if name == "Summary":
                ws.set_row(6, 135)


def write_pdf(pdf_path, summary, mut_counts, tree_pruned):
    with PdfPages(pdf_path) as pdf:
        fig = plt.figure(figsize=(8.5, 11))
        lines = [
            f"Input: {summary['input_name']}",
            f"Sequence records: {summary['n_records']:,}",
            f"Window: {summary['start_residue']}-{summary['end_residue']}",
            f"Reference: {summary['reference_id']}",
            "",
            METHOD,
            "",
            "Quality and interpretation:",
            *summary["warnings"],
        ]
        wrapped = [part for line in lines for part in (textwrap.wrap(str(line), 85) or [""])]
        for offset in range(0, len(wrapped), 45):
            fig.text(
                0.08, 0.94, "FluTrees analysis report", fontsize=20, weight="bold", color="#163849"
            )
            fig.text(
                0.08,
                0.89,
                "\n".join(wrapped[offset : offset + 45]),
                va="top",
                fontsize=10,
                family="monospace",
                linespacing=1.5,
                parse_math=False,
            )
            pdf.savefig(fig)
            fig.clear()
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(11, 8.5))
        top = mut_counts.head(25).iloc[::-1]
        ax.barh(top["mutations"], top["count"], color="#24766c")
        ax.set_xlabel("Sequence records with a called substitution")
        ax.set_title("Most frequent substitutions" if len(top) else "No substitutions were called")
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)
        pages = tree_pages(tree_pruned)
        mapping = {nodes[0].node_id: i for i, nodes in enumerate(pages, 1)}
        for i, nodes in enumerate(pages, 1):
            fig = tree_figure(
                nodes, tree_pruned.support, "Pruned mutation decision tree", i, mapping
            )
            pdf.savefig(fig)
            plt.close(fig)


STYLE = """body{font:17px system-ui,sans-serif;color:#163849;background:#f5f8fa;max-width:1100px;margin:auto;padding:32px}
h1{font-size:34px}a{color:#075e72}nav{display:flex;gap:12px;flex-wrap:wrap}nav a{padding:12px 18px;background:#d9eee8;border-radius:8px;text-decoration:none}
section,details{background:white;border:1px solid #d7e0e7;border-radius:8px;padding:16px;margin:14px 0}
summary{cursor:pointer;font-weight:650}details details{margin-left:22px;border-left:3px solid #4d8d7a}
table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:8px;border-bottom:1px solid #e0e7ed;overflow-wrap:anywhere}
img{max-width:100%}.note{color:#48616e;font-size:15px}.records{max-height:260px;overflow:auto}li{margin:8px 0}
@media print{details{break-inside:avoid}nav{display:none}}"""


def write_html(outpath, summary, full, pruned, metadata):
    def esc(value):
        return html.escape(str(value), quote=True)

    names = dict(zip(metadata.record_id, metadata.strain))

    def node_html(node):
        details = "".join(node_html(c) for c in (node.left, node.right) if c is not None)
        records = "".join(
            f"<tr><td>{esc(r)}</td><td>{esc(names[r])}</td></tr>" for r in sorted(node.seqs)
        )
        note = node.stop_reason
        if not note and node.support > sum(
            c.support for c in (node.left, node.right) if c is not None
        ):
            note = "Some or all descendant groups are hidden by pruning. Use the full tree to see them."
        return (
            f"<details open><summary>#{node.node_id} {esc(node.label)} — {node.support:,} records "
            f'({node.support / full.support:.1%} of input)</summary><p class="note">{esc(note)}</p>'
            f'<details><summary>Show records in this group</summary><div class="records"><table><thead><tr><th>Record ID</th><th>Strain</th></tr></thead>'
            f"<tbody>{records}</tbody></table></div></details>{details}</details>"
        )

    warnings = "".join(f"<li>{esc(w)}</li>" for w in summary["warnings"])
    document = (
        f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>FluTrees — {esc(summary['input_name'])}</title><style>{STYLE}</style><body>"
        f"<h1>Your FluTrees results</h1><p>{esc(summary['input_name'])} · {summary['n_records']:,} sequence records</p>"
        '<nav><a href="report.pdf">Read the PDF report</a><a href="results.xlsx">Open Excel workbook</a>'
        '<a href="#pruned">Explore simplified tree</a><a href="#full">Explore full tree</a></nav>'
        "<section><h2>Start here</h2><p>Read the PDF for an overview. Use Excel to filter records and mutations. "
        "Click a group below to collapse it, or “Show records” to inspect its members. Use your browser’s Find "
        "command (Ctrl+F or Command+F) to search visible text; open a group’s records to search them.</p>"
        '<p>For a presentation, use <a href="tree_pruned.png">PNG</a> or editable <a href="tree_pruned.svg">SVG</a>. '
        'These show the overview page. <a href="tree_pruned.pdf">Simplified tree PDF</a> and '
        '<a href="tree_full.pdf">full tree PDF</a> include every continuation page. Additional page images are in this folder.</p></section>'
        f"<section><h2>How to interpret this run</h2><p>{esc(METHOD)}</p><p>Window: {summary['start_residue']}–{summary['end_residue']}. "
        f"Reference record: {esc(summary['reference_id'])}</p><ul>{warnings}</ul></section>"
        '<section><h2>Tree overview</h2><img src="tree_pruned.svg" alt="Pruned mutation decision tree overview"></section>'
        f'<h2 id="pruned">Simplified tree</h2>{node_html(pruned)}<h2 id="full">Full tree</h2>{node_html(full)}'
        '<p class="note">The workbook Node Membership sheet connects each node ID to its records. The JSON, TSV, '
        "and FASTA files retain the underlying data. This page works offline without uploading sequences.</p></body></html>"
    )
    outpath.write_text(document, encoding="utf-8")
