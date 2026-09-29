"""Read legacy-compatible JSON trees with explicit structural validation."""

import json
from pathlib import Path
from typing import Any, Mapping, Set

from .tree_build import Node


def from_dict(data: Mapping[str, Any]) -> Node:
    """Restore topology, membership and path state from a full or pruned tree.

    The existing export schema is retained. A pruned node may have one child;
    two visible children must partition their parent exactly. Path-state sets
    are reconstructed rather than trusted from unvalidated serialized input.
    """
    seen: Set[int] = set()

    def restore(value, depth, used):
        if not isinstance(value, dict):
            raise ValueError("Every tree node must be a JSON object.")
        required = {"node_id", "depth", "label", "support", "record_ids", "stop_reason", "left", "right"}
        if not required.issubset(value):
            raise ValueError("Tree node is missing required fields.")
        for key in ("node_id", "depth", "support"):
            if type(value[key]) is not int:
                raise ValueError(f"Tree {key} must be an integer, not a Boolean or string.")
        node_id = value["node_id"]
        if node_id < 1 or node_id in seen:
            raise ValueError("Tree node IDs must be positive and unique.")
        seen.add(node_id)
        if value["depth"] != depth or depth > 20:
            raise ValueError("Tree depths must start at zero and advance one level per edge, up to 20.")
        if not isinstance(value["label"], str) or not isinstance(value["stop_reason"], str):
            raise ValueError("Tree labels and stopping reasons must be strings.")
        records = value["record_ids"]
        if not isinstance(records, list) or any(not isinstance(r, str) or not r for r in records):
            raise ValueError("Tree record_ids must be a list of nonempty strings.")
        seqs = set(records)
        if not records or len(seqs) != len(records) or value["support"] != len(records):
            raise ValueError("Tree support must match unique, nonempty record membership.")
        node = Node(node_id, depth, value["label"], len(seqs), seqs, set(used),
                    stop_reason=value["stop_reason"])
        children = []
        for side in ("left", "right"):
            child_data = value[side]
            if child_data is None:
                continue
            if not isinstance(child_data, dict) or not isinstance(child_data.get("label"), str):
                raise ValueError("Tree children must have string labels.")
            label = child_data["label"]
            mutation = label[4:] if side == "right" and label.startswith("Not ") else label
            if not mutation or mutation in used:
                raise ValueError("A mutation decision cannot repeat along a tree path.")
            child = restore(child_data, depth + 1, used | {mutation})
            if not child.seqs < seqs:
                raise ValueError("A child must contain a nonempty proper subset of its parent's records.")
            setattr(node, side, child)
            children.append(child)
        if len(children) == 2:
            left, right = children
            if right.label != f"Not {left.label}":
                raise ValueError("Positive and negative child labels must describe the same substitution.")
            if left.seqs & right.seqs or left.seqs | right.seqs != seqs:
                raise ValueError("Children must be disjoint and conserve their parent's records.")
        return node

    return restore(data, 0, set())


def read_tree(path: Path) -> Node:
    """Load and validate a UTF-8 JSON tree exported by FluTrees."""
    return from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
