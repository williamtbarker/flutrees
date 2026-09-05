from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional, Set

import pandas as pd

@dataclass
class Node:
    node_id: int
    depth: int
    label: str          # "Root", "A123T", "Not A123T"
    support: int        # number of records at this node
    seqs: Set[str]      # record_ids in this node
    used: Set[str]      # mutations already used along this path
    left: Optional["Node"] = None
    right: Optional["Node"] = None

def build_tree(mutation_df: pd.DataFrame, max_depth: int, min_split: int, min_freq: float) -> Node:
    """
    mutation_df: columns record_id, mutations(list[str])
    """
    if not {"record_id", "mutations"}.issubset(set(mutation_df.columns)):
        raise ValueError("mutation_df must have columns: record_id, mutations")

    # mutation -> set(record_id)
    mut_to_ids: Dict[str, Set[str]] = {}
    all_ids: Set[str] = set(mutation_df["record_id"].tolist())

    for _, row in mutation_df.iterrows():
        rid = row["record_id"]
        muts = row["mutations"] if isinstance(row["mutations"], list) else []
        for m in muts:
            mut_to_ids.setdefault(m, set()).add(rid)

    next_id = 1
    root = Node(node_id=next_id, depth=0, label="Root", support=len(all_ids), seqs=all_ids, used=set())
    next_id += 1

    def pick_split(node: Node) -> Optional[str]:
        n = node.support
        if n < (2 * min_split):
            return None
        freq_thresh = max(int(min_freq * n), min_split)

        best_m = None
        best_w = -1
        for m, have_ids in mut_to_ids.items():
            if m in node.used:
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
            return
        m = pick_split(node)
        if m is None:
            return

        have = node.seqs & mut_to_ids.get(m, set())
        not_have = node.seqs - have
        if len(have) < min_split or len(not_have) < min_split:
            return

        used2 = set(node.used)
        used2.add(m)

        node.left = Node(node_id=next_id, depth=node.depth+1, label=m, support=len(have), seqs=have, used=used2)
        next_id += 1
        node.right = Node(node_id=next_id, depth=node.depth+1, label=f"Not {m}", support=len(not_have), seqs=not_have, used=used2)
        next_id += 1

        rec(node.left)
        rec(node.right)

    rec(root)
    return root

def prune_tree(root: Node, prune_cutoff: int) -> Node:
    def clone(n: Node) -> Optional[Node]:
        if n.depth != 0 and n.support < prune_cutoff:
            return None
        out = Node(node_id=n.node_id, depth=n.depth, label=n.label, support=n.support, seqs=set(), used=set())
        out.left = clone(n.left) if n.left else None
        out.right = clone(n.right) if n.right else None
        return out
    pr = clone(root)
    return pr if pr is not None else root

def to_dict(n: Node) -> Dict[str, Any]:
    return {
        "node_id": n.node_id,
        "depth": n.depth,
        "label": n.label,
        "support": n.support,
        "left": to_dict(n.left) if n.left else None,
        "right": to_dict(n.right) if n.right else None,
    }

def iter_nodes(n: Node) -> Iterator[Node]:
    yield n
    if n.left: yield from iter_nodes(n.left)
    if n.right: yield from iter_nodes(n.right)
