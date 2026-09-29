"""Round-trip all published tree views without losing partitions or path state."""

import copy
import json

import pandas as pd
import pytest

from flutrees.exports import group_assignments, write_tree
from flutrees.tree_build import build_tree, iter_nodes, prune_tree, to_dict
from flutrees.tree_io import from_dict, read_tree


@pytest.fixture
def source_tree():
    data = pd.DataFrame({
        "record_id": [str(i) for i in range(16)],
        "mutations": [[f"A{j+1}T" for j in range(4) if i & (1 << j)] for i in range(16)],
    })
    return data


@pytest.mark.parametrize("mode", ["frequency", "balanced", "diversity"])
@pytest.mark.parametrize("cutoff", [1, 3, 17])
def test_tree_json_roundtrip(tmp_path, source_tree, mode, cutoff):
    original = prune_tree(build_tree(source_tree, 5, 1, 0, mode), cutoff)
    path = tmp_path / "tree.json"
    write_tree(path, original)
    restored = read_tree(path)
    assert to_dict(restored) == to_dict(original)
    assert [(n.node_id, n.used) for n in iter_nodes(restored)] == [(n.node_id, n.used) for n in iter_nodes(original)]
    pd.testing.assert_frame_equal(group_assignments(restored), group_assignments(original))
    write_tree(tmp_path / "again.json", restored)
    assert path.read_bytes() == (tmp_path / "again.json").read_bytes()


def test_asymmetric_pruned_tree_and_isolated_state(source_tree):
    full = build_tree(source_tree, 2, 1, 0)
    full.left = None
    restored = from_dict(to_dict(full))
    assert restored.left is None and restored.right.used == {"A1T"}
    restored.right.seqs.pop()
    assert len(full.right.seqs) == 8
    data = to_dict(full)
    data["right"]["label"] = "alternate"
    assert from_dict(data).right.used == {"alternate"}


@pytest.mark.parametrize("key,value", [
    ("node_id", True), ("depth", "0"), ("support", 2.0), ("node_id", 0),
    ("depth", -1), ("label", None), ("stop_reason", []), ("record_ids", "abc"),
    ("record_ids", [None]), ("record_ids", [""]), ("record_ids", []),
    ("record_ids", ["0", "0"]), ("support", 999),
    ("left", []), ("right", {"label": None}),
])
def test_invalid_fields_are_rejected(source_tree, key, value):
    tree = to_dict(build_tree(source_tree, 2, 1, 0))
    tree[key] = value
    with pytest.raises(ValueError):
        from_dict(tree)


def test_invalid_structure_and_membership(source_tree):
    base = to_dict(build_tree(source_tree, 3, 1, 0))
    invalid = [None, {}, {"node_id": 1}]
    data = copy.deepcopy(base); data["left"]["node_id"] = data["node_id"]; invalid.append(data)
    data = copy.deepcopy(base); data["left"]["depth"] = 0; invalid.append(data)
    data = copy.deepcopy(base); data["left"]["label"] = ""; invalid.append(data)
    data = copy.deepcopy(base); data["left"]["left"]["label"] = data["left"]["label"]; invalid.append(data)
    data = copy.deepcopy(base); data["right"]["label"] = "Not A999T"; invalid.append(data)
    data = copy.deepcopy(base); data["left"]["record_ids"][0] = "outside"; invalid.append(data)
    # Valid individual leaf nodes but an invalid parent partition.
    data = copy.deepcopy(base)
    for child in (data["left"], data["right"]):
        child["left"] = child["right"] = None
    data["right"]["record_ids"] = data["left"]["record_ids"].copy(); invalid.append(data)
    data = copy.deepcopy(base)
    data["left"]["left"] = data["left"]["right"] = None
    data["left"]["record_ids"] = data["record_ids"].copy()
    data["left"]["support"] = data["support"]; invalid.append(data)
    for data in invalid:
        with pytest.raises(ValueError):
            from_dict(data)


def test_invalid_json_and_depth_limit(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{")
    with pytest.raises(json.JSONDecodeError):
        read_tree(path)
    data = {"node_id": 1, "depth": 0, "support": 23, "label": "Root", "record_ids": list(map(str, range(23))),
            "stop_reason": "", "left": None, "right": None}
    node = data
    for depth in range(1, 22):
        child = {"node_id": depth+1, "depth": depth, "support": 23-depth, "label": f"A{depth}T",
                 "record_ids": list(map(str, range(23-depth))), "stop_reason": "", "left": None, "right": None}
        node["left"] = child
        node = child
    with pytest.raises(ValueError, match="depths"):
        from_dict(data)
