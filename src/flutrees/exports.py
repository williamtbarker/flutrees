"""Portable, human-readable results backed by one shared set of tables."""

import html
import json
import textwrap
from pathlib import Path
from typing import Any

import pandas as pd
from .layout import FigureStyle, FIGURE_FIELDS
from .figures import tree_figure, tree_pages
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from .tree_build import to_dict, iter_nodes
from .strategies import DESCRIPTIONS

EXCEL_DATA_ROWS = 1_048_575  # Excel row limit minus the header.


METHOD = (
    "Mutation decision tree, not a phylogeny. Counts represent sequence records, including duplicates. "
    "Reference: most common aligned sequence; ties use first input occurrence. Positions count ungapped "
    "reference residues starting at the selected window start, not standardized HA numbering. "
    "Reference-gap columns are ignored (substitutions only). Splits at positions with missing or ambiguous "
    "observations in that node are withheld. Input sequences must share a consistent numbering convention."
)


def method_text(summary):
    text = METHOD
    if summary.get("reference_method") == "explicit":
        text = text.replace("most common aligned sequence; ties use first input occurrence", "explicitly selected input record")
    return text + " " + DESCRIPTIONS[summary.get("tree_strategy", "frequency")]


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


def write_text_tree(outpath, tree, summary, view):
    """A complete, monospaced trace with the same node IDs as every other export."""
    lines = [
        f"FluTrees - {view} mutation decision tree",
        f"Input: {summary['input_name']}",
        f"Reference: {summary['reference_id']}",
        f"Window: {summary['start_residue']}-{summary['end_residue']}",
        "", textwrap.fill(method_text(summary), 100), "",
        "Read top to bottom; indentation shows parent/child relationships.",
        "Percentages use all input records. Match #node IDs to Excel or node_membership.tsv.",
        "",
    ]

    def walk(node, prefix="", connector=""):
        lines.append(
            f"{prefix}{connector}#{node.node_id} {node.label} | "
            f"{node.support:,} records | {node.support / tree.support:.1%} of input"
        )
        indent = prefix
        if connector:
            indent += "    " if connector == "`-- " else "|   "
        if node.stop_reason:
            lines.append(f"{indent}Stop: {node.stop_reason}")
        children = [c for c in (node.left, node.right) if c is not None]
        for i, child in enumerate(children):
            walk(child, indent, "`-- " if i == len(children) - 1 else "+-- ")

    walk(tree)
    outpath.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_dot_tree(outpath, tree, mode=""):
    """Export decision-tree nodes and edges in Graphviz DOT format."""
    lines = [
        "digraph FluTrees {",
        '  graph [rankdir=LR, label="Mutation decision tree - record counts, not confidence", labelloc=t];',
        '  node [shape=box, style="rounded,filled", fillcolor="#d9f0e7"];',
        '  edge [arrowhead=none];',
    ]
    for node in iter_nodes(tree):
        label = f"#{node.node_id} {node.label}\n{node.support:,} records ({node.support / tree.support:.1%} of input)"
        if node.stop_reason:
            label += "\n" + node.stop_reason
        lines.append(f"  n{node.node_id} [label={json.dumps(label, ensure_ascii=False)}];")
        for child in (node.left, node.right):
            if child is not None:
                lines.append(f"  n{node.node_id} -> n{child.node_id};")
    lines.append("}")
    if mode:
        lines.insert(1, "  // Split strategy: " + mode)
    outpath.write_text("\n".join(lines) + "\n", encoding="utf-8")


def group_assignments(tree):
    """Exactly one terminal full-tree group and complete decision path per record."""
    rows: list[dict[str, Any]] = []

    def walk(node, path):
        path = path + [node.label]
        children = [c for c in (node.left, node.right) if c is not None]
        if not children:
            rows.extend(
                {"record_id": rid, "full_group_id": node.node_id,
                 "full_group_size": node.support, "full_group_path": " > ".join(path)}
                for rid in sorted(node.seqs)
            )
        for child in children:
            walk(child, path)

    walk(tree, [])
    return pd.DataFrame(rows)


def node_tables(tree_full, tree_pruned):
    rows: list[dict[str, Any]] = []
    members: list[dict[str, Any]] = []
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


def write_workbook(outpath, summary, metadata, mutations, counts, full, pruned, extra_sheets=None):
    nodes, members = node_tables(full, pruned)
    records = metadata.merge(flat_mutations(mutations), on="record_id", validate="one_to_one")
    records = records.merge(group_assignments(full), on="record_id", validate="one_to_one")
    first_columns = ["record_id", "full_group_id", "full_group_size", "full_group_path"]
    records = records[first_columns + [c for c in records.columns if c not in first_columns]]
    summary_rows = [
        ("Input", summary["input_name"]),
        ("Sequence records", summary["n_records"]),
        ("Reference", summary["reference_id"]),
        ("Residue window", f"{summary['start_residue']}-{summary['end_residue']}"),
        (
            "How to use",
            "Filter Records by full_group_id to select a final group; full_group_path traces every decision. Node Membership also includes intermediate groups.",
        ),
        ("Interpretation", method_text(summary)),
        ("Large tables", "Tables exceeding one worksheet continue on numbered sheets. No records are dropped."),
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
    if extra_sheets is not None:
        sheets.update(extra_sheets)
    with pd.ExcelWriter(
        outpath,
        engine="xlsxwriter",
        engine_kwargs={"options": {"strings_to_formulas": False, "strings_to_urls": False}},
    ) as writer:
        wrap = writer.book.add_format({"text_wrap": True, "valign": "top"})
        for name, df in sheets.items():
            for column in df.select_dtypes(include=["object", "string"]):
                if df[column].astype(str).str.len().gt(32_767).any():
                    raise ValueError(
                        f"Excel cell limit exceeded in {name}, column {column}. "
                        "A value is longer than 32,767 characters; shorten the input header or window. "
                        "Complete values remain in the diagnostic TSV files."
                    )
            for number, start in enumerate(range(0, max(1, len(df)), EXCEL_DATA_ROWS), 1):
                suffix = f" ({number})" if number > 1 else ""
                sheet_name = name[:31 - len(suffix)] + suffix
                part = df.iloc[start:start + EXCEL_DATA_ROWS]
                part.to_excel(writer, sheet_name=sheet_name, index=False)
                ws = writer.sheets[sheet_name]
                ws.freeze_panes(1, 0)
                ws.set_column(0, len(df.columns) - 1, 24)
                if not part.empty:
                    ws.add_table(
                        0, 0, len(part), len(df.columns) - 1,
                        {"columns": [{"header": c} for c in df.columns], "style": "Table Style Medium 2"},
                    )
                if name in {"Summary", "QC"}:
                    ws.set_column(len(df.columns) - 1, len(df.columns) - 1, 105, wrap)
                    ws.set_default_row(60)
                if name == "Records":
                    ws.set_column(3, 3, 70, wrap)
                if name == "Summary":
                    ws.set_row(6, 135)


def write_pdf(pdf_path, summary, mut_counts, tree_pruned, family=None):
    with PdfPages(pdf_path) as pdf:
        fig = plt.figure(figsize=(8.5, 11))
        lines = [
            f"Input: {summary['input_name']}",
            f"Sequence records: {summary['n_records']:,}",
            f"Window: {summary['start_residue']}-{summary['end_residue']}",
            f"Reference: {summary['reference_id']}",
            "",
            method_text(summary),
            "",
            "Quality and interpretation:",
            *summary["warnings"],
        ]
        if len(summary.get("tree_modes", [])) > 1:
            lines.extend(["", "Tree views share one alignment and mutation call set:"])
            lines.extend(DESCRIPTIONS[mode] for mode in summary["tree_modes"])
            lines.append("These exploratory views are not competing evolutionary reconstructions or confidence estimates.")
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
        views = family or {summary.get("tree_strategy", "frequency"): (tree_pruned, tree_pruned)}
        for mode, (_, tree) in views.items():
            pages = tree_pages(tree)
            mapping = {nodes[0].node_id: i for i, nodes in enumerate(pages, 1)}
            for i, nodes in enumerate(pages, 1):
                fig = tree_figure(nodes, tree.support, f"{mode.title()}: Pruned mutation decision tree", i, mapping,
                                  FigureStyle(**{k: v for k, v in summary["config"].items() if k in FIGURE_FIELDS}))
                pdf.savefig(fig)
                plt.close(fig)


STYLE = """body{font:17px system-ui,sans-serif;color:#163849;background:#f5f8fa;max-width:1100px;margin:auto;padding:32px}
h1{font-size:34px}a{color:#075e72}nav{display:flex;gap:12px;flex-wrap:wrap}nav a{padding:12px 18px;background:#d9eee8;border-radius:8px;text-decoration:none}
section,details{background:white;border:1px solid #d7e0e7;border-radius:8px;padding:16px;margin:14px 0}
summary{cursor:pointer;font-weight:650}details details{margin-left:22px;border-left:3px solid #4d8d7a}
table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:8px;border-bottom:1px solid #e0e7ed;overflow-wrap:anywhere}
img{max-width:100%}.note{color:#48616e;font-size:15px}.records{max-height:260px;overflow:auto}li{margin:8px 0}
@media print{details{break-inside:avoid}nav{display:none}}"""


def write_html(outpath, summary, full, pruned, metadata, family=None, comparisons=None):
    def esc(value):
        return html.escape(str(value), quote=True)

    names = dict(zip(metadata.record_id, metadata.strain))

    def node_html(node):
        details = "".join(node_html(c) for c in (node.left, node.right) if c is not None)
        records = "".join(
            f"<tr><td>{esc(r)}</td><td>{esc(names[r])}</td></tr>" for r in sorted(node.seqs)
        )
        note = node.stop_reason
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
        '<a href="tree_full.pdf">full tree PDF</a> include every continuation page. Additional page images are in this folder.</p>'
        '<p>For a plain-text trace, open the <a href="tree_full.txt">full text tree</a> or '
        '<a href="tree_pruned.txt">simplified text tree</a>. For custom diagram layouts, use the '
        '<a href="tree_full.dot">full Graphviz graph</a> or <a href="tree_pruned.dot">simplified Graphviz graph</a>.</p>'
        '<p>In Excel Records, filter <strong>full_group_id</strong> to select a final group; '
        '<strong>full_group_path</strong> shows every decision leading to it. These assignments are also in '
        '<a href="group_assignments.tsv">group_assignments.tsv</a>. Group IDs are local to this run and can change between runs.</p></section>'
        f"<section><h2>How to interpret this run</h2><p>{esc(method_text(summary))}</p><p>Window: {summary['start_residue']}–{summary['end_residue']}. "
        f"Reference record: {esc(summary['reference_id'])}</p><ul>{warnings}</ul></section>"
        '<section><h2>Tree overview</h2><img src="tree_pruned.svg" alt="Pruned mutation decision tree overview"></section>'
        f'<h2 id="pruned">Simplified tree</h2>{node_html(pruned)}<h2 id="full">Full tree</h2>{node_html(full)}'
        '<p class="note">The workbook Node Membership sheet connects each node ID to its records. The JSON, TSV, '
        "and FASTA files retain the underlying data. This page works offline without uploading sequences.</p></body></html>"
    )
    if family is not None:
        panels = ['<section><h2>Compare tree views</h2><p>These exploratory views share one alignment, reference, and set of mutation observations. Differences reflect split rules, not evolutionary histories or confidence estimates. Root-level tree files use the primary mode shown above. Group IDs are local to each mode.</p>']
        if comparisons is not None:
            panels.append(comparisons.to_html(index=False, escape=True, border=0))
        for mode, (mode_full, mode_pruned) in family.items():
            panels.append(f'<h3>{esc(DESCRIPTIONS[mode])}</h3><p><a href="trees/{mode}/tree_full.pdf">Full PDF</a> | <a href="trees/{mode}/tree_pruned.pdf">Simplified PDF</a> | <a href="trees/{mode}/tree_full.txt">Text trace</a> | <a href="trees/{mode}/group_assignments.tsv">Group assignments</a></p>')
            if mode != summary.get("tree_strategy", "frequency"):
                panels.append(node_html(mode_pruned))
                panels.append('<details><summary>Full ' + esc(mode) + ' tree</summary>' + node_html(mode_full) + '</details>')
        panels.append('<p>Cross-mode tables: <a href="tree_comparison.tsv">Tree comparison</a>, <a href="tree_groups.tsv">tree groups</a>, <a href="mutation_use.tsv">mutation use</a>. In multi-mode workbooks, use Tree Groups and All Membership with the mode column.</p></section>')
        document = document.replace('<section><h2>Tree overview', "".join(panels) + '<section><h2>Tree overview')
    outpath.write_text(document, encoding="utf-8")
