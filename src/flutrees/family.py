"""Aligned-data tree families, comparison tables, and portable tree artifacts."""

import shutil

import pandas as pd

from .exports import (group_assignments, node_tables, write_dot_tree, write_node_summary,
                      write_summary, write_text_tree, write_tree)
from .figures import tree_pages, write_tree_figures
from .strategies import DESCRIPTIONS, STRATEGY_VERSION
from .tree_build import build_tree, iter_nodes, prune_tree

TREE_SUFFIXES = ("pdf", "json", "txt", "dot", "svg", "png")


def build_family(cfg, mutations, primary_full, primary_pruned):
    primary = cfg.tree_modes()[0]
    family = {primary: (primary_full, primary_pruned)}
    for mode in cfg.tree_modes()[1:]:
        full = build_tree(mutations, cfg.max_depth, cfg.min_split, cfg.min_freq, strategy=mode)
        family[mode] = (full, prune_tree(full, cfg.prune_cutoff))
    return family


def comparison_tables(family):
    comparisons, assignments, node_frames, member_frames, uses = [], [], [], [], []
    for mode, (full, pruned) in family.items():
        nodes = list(iter_nodes(full))
        leaves = [node for node in nodes if node.left is None and node.right is None]
        comparisons.append({
            "mode": mode, "root_split": full.left.label if full.left else "No split",
            "positive_records": full.left.support if full.left else 0,
            "negative_records": full.right.support if full.right else 0,
            "terminal_groups": len(leaves), "maximum_depth": max(node.depth for node in nodes),
            "full_nodes": len(nodes), "hidden_nodes": len(nodes) - len(list(iter_nodes(pruned))),
        })
        assignments.append(group_assignments(full).assign(mode=mode))
        node_df, member_df = node_tables(full, pruned)
        node_frames.append(node_df.assign(mode=mode))
        member_frames.append(member_df.assign(mode=mode))
        used = {}
        for node in nodes:
            if node.left is not None:
                label = node.left.label
                entry = used.setdefault(label, {"mode": mode, "mutation": label,
                                               "first_depth": node.depth + 1, "split_occurrences": 0})
                entry["first_depth"] = min(entry["first_depth"], node.depth + 1)
                entry["split_occurrences"] += 1
        uses.extend(used.values())
    return {
        "Tree Comparison": pd.DataFrame(comparisons),
        "Tree Groups": pd.concat(assignments, ignore_index=True),
        "Mutation Use": pd.DataFrame(uses, columns=["mode", "mutation", "first_depth", "split_occurrences"]),
        "All Nodes": pd.concat(node_frames, ignore_index=True),
        "All Membership": pd.concat(member_frames, ignore_index=True),
    }


def expected_tree_files(tree, view):
    stem = f"tree_{view}"
    paths = [f"{stem}.{suffix}" for suffix in TREE_SUFFIXES]
    for page in range(2, len(tree_pages(tree)) + 1):
        paths.extend(f"{stem}_page_{page:03d}.{suffix}" for suffix in ("svg", "png"))
    return paths


def write_family(out, family, summary, tables):
    """Reuse primary visual artifacts; never realign or call mutations per view."""
    expected = []
    primary = next(iter(family))
    for mode, (full, pruned) in family.items():
        destination = out / "trees" / mode
        destination.mkdir(parents=True)
        method = {"mode": mode, "strategy_version": STRATEGY_VERSION,
                  "description": DESCRIPTIONS[mode], "analysis_id": summary["analysis_id"],
                  "reference_id": summary["reference_id"], "coordinate_system": summary["coordinate_system"]}
        write_summary(destination / "method.json", method)
        mode_summary = {**summary, "tree_strategy": mode}
        for view, tree in (("full", full), ("pruned", pruned)):
            paths = expected_tree_files(tree, view)
            if mode == primary:
                for path in paths:
                    shutil.copyfile(out / path, destination / path)
                    expected.append(path)
            else:
                write_tree(destination / f"tree_{view}.json", tree)
                write_text_tree(destination / f"tree_{view}.txt", tree, mode_summary, view)
                write_dot_tree(destination / f"tree_{view}.dot", tree, mode)
                write_tree_figures(destination, tree, f"tree_{view}", mode)
            expected.extend(f"trees/{mode}/{path}" for path in paths)
        group_assignments(full).to_csv(destination / "group_assignments.tsv", sep="\t", index=False)
        write_node_summary(destination / "node_summary.tsv", full, pruned)
        expected.extend(f"trees/{mode}/{path}" for path in (
            "method.json", "group_assignments.tsv", "node_summary.tsv", "node_membership.tsv"))
    for name, table in tables.items():
        filename = name.lower().replace(" ", "_") + ".tsv"
        table.to_csv(out / filename, sep="\t", index=False)
        expected.append(filename)
    return expected
