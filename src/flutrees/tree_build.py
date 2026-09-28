from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Dict, Iterator, Optional, Set

import pandas as pd


@dataclass
class Node:
    node_id: int
    depth: int
    label: str  # "Root", "A123T", "Not A123T"
    support: int  # number of records at this node
    seqs: Set[str]  # record_ids in this node
    used: Set[str]  # mutations already used along this path
    left: Optional["Node"] = None
    right: Optional["Node"] = None
    stop_reason: str = ""


def build_tree(mutation_df: pd.DataFrame, max_depth: int, min_split: int, min_freq: float) -> Node:
    """
    mutation_df: columns record_id, mutations(list[str])
    """
    if not {"record_id", "mutations"}.issubset(set(mutation_df.columns)):
        raise ValueError("mutation_df must have columns: record_id, mutations")
    if mutation_df.empty or mutation_df.record_id.duplicated().any():
        raise ValueError("Tree input must contain unique record IDs and at least one record.")
    if not 0 <= max_depth <= 20 or min_split < 1 or not 0 <= min_freq <= 0.5:
        raise ValueError("Invalid tree settings.")

    # mutation -> set(record_id)
    mut_to_ids: Dict[str, Set[str]] = {}
    all_ids: Set[str] = set(mutation_df["record_id"].tolist())
    unknown: Dict[int, Set[str]] = {}

    for _, row in mutation_df.iterrows():
        rid = row["record_id"]
        muts = row["mutations"] if isinstance(row["mutations"], list) else []
        for m in muts:
            mut_to_ids.setdefault(m, set()).add(rid)
        for pos in row.get("uncertain_positions", []):
            unknown.setdefault(pos, set()).add(rid)

    next_id = 1
    root = Node(
        node_id=next_id, depth=0, label="Root", support=len(all_ids), seqs=all_ids, used=set()
    )
    next_id += 1

    def pick_split(node: Node) -> Optional[str]:
        n = node.support
        if n < (2 * min_split):
            return None
        freq_thresh = max(ceil(min_freq * n), min_split)

        best_m = None
        best_w = -1
        for m, have_ids in mut_to_ids.items():
            if m in node.used:
                continue
            if node.seqs & unknown.get(int(m[1:-1]), set()):
                continue
            have = node.seqs & have_ids
            w = len(have)
            if w < freq_thresh:
                continue
            if (n - w) < freq_thresh:
                continue
            if w > best_w:
                best_w = w
                best_m = m
        return best_m

    def rec(node: Node):
        nonlocal next_id
        if node.depth >= max_depth:
            node.stop_reason = "Maximum depth reached."
            return
        m = pick_split(node)
        if m is None:
            node.stop_reason = "No eligible split: counts, frequency, or incomplete observations limit subdivision."
            return

        have = node.seqs & mut_to_ids.get(m, set())
        not_have = node.seqs - have

        used2 = set(node.used)
        used2.add(m)

        node.left = Node(
            node_id=next_id, depth=node.depth + 1, label=m, support=len(have), seqs=have, used=used2
        )
        next_id += 1
        node.right = Node(
            node_id=next_id,
            depth=node.depth + 1,
            label=f"Not {m}",
            support=len(not_have),
            seqs=not_have,
            used=used2,
        )
        next_id += 1

        rec(node.left)
        rec(node.right)

    rec(root)
    return root


def prune_tree(root: Node, prune_cutoff: int) -> Node:
    if prune_cutoff < 1:
        raise ValueError("Pruning cutoff must be at least 1.")
    out = Node(
        root.node_id,
        root.depth,
        root.label,
        root.support,
        set(root.seqs),
        set(root.used),
        stop_reason=root.stop_reason,
    )
    for side in ("left", "right"):
        child = getattr(root, side)
        if child is not None and child.support >= prune_cutoff:
            setattr(out, side, prune_tree(child, prune_cutoff))
    return out


def to_dict(n: Node) -> Dict[str, Any]:
    return {
        "node_id": n.node_id,
        "depth": n.depth,
        "label": n.label,
        "support": n.support,
        "record_ids": sorted(n.seqs),
        "stop_reason": n.stop_reason,
        "left": to_dict(n.left) if n.left else None,
        "right": to_dict(n.right) if n.right else None,
    }


def iter_nodes(n: Node) -> Iterator[Node]:
    yield n
    if n.left:
        yield from iter_nodes(n.left)
    if n.right:
        yield from iter_nodes(n.right)
