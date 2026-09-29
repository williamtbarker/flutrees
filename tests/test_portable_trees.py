"""Verify portable trees and scientist-facing group assignments against known groups."""

import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

import pandas as pd
import pytest
from openpyxl import load_workbook

from flutrees import pipeline
from flutrees.exports import group_assignments, write_text_tree, write_dot_tree
from flutrees.tree_build import build_tree, iter_nodes, prune_tree


@pytest.fixture
def branching_tree():
    mutations = ["A1T", "C2D", "E3F"]
    data = pd.DataFrame({
        "record_id": [str(i) for i in range(8)],
        "mutations": [[m for b, m in enumerate(mutations) if i & (1 << b)] for i in range(8)],
    })
    return build_tree(data, 5, 1, 0)


def test_complete_text_trace_and_record_paths(tmp_path, branching_tree):
    summary = {"input_name": "test.fasta", "reference_id": "ref", "start_residue": 1, "end_residue": 3}
    write_text_tree(tmp_path / "tree.txt", branching_tree, summary, "full")
    text = (tmp_path / "tree.txt").read_text()
    ids = [int(x) for x in re.findall(r"#(\d+) [^\n]+ \|", text)]
    assert ids == [n.node_id for n in iter_nodes(branching_tree)]
    assert len(ids) == len(set(ids)) == 15
    assert "Window: 1-3" in text and "not a phylogeny" in text
    assert "+-- #2 A1T | 4 records | 50.0%" in text
    assert "|   +-- " in text and "`-- " in text
    assert text.count("Stop: ") == 8
    groups = group_assignments(branching_tree).set_index("record_id")
    assert sorted(groups.index) == list(map(str, range(8)))
    assert groups.full_group_id.nunique() == 8
    assert groups.full_group_size.tolist() == [1] * 8
    mutations = ["A1T", "C2D", "E3F"]
    for i in range(8):
        expected = "Root > " + " > ".join(m if i & (1 << b) else f"Not {m}" for b, m in enumerate(mutations))
        assert groups.loc[str(i), "full_group_path"] == expected


def test_root_only_and_pruned_traces_keep_explanations(tmp_path, branching_tree):
    summary = {"input_name": "test.fasta", "reference_id": "ref", "start_residue": 1, "end_residue": 3}
    pruned = prune_tree(branching_tree, 9)
    write_text_tree(tmp_path / "pruned.txt", pruned, summary, "pruned")
    text = (tmp_path / "pruned.txt").read_text()
    assert "#1 Root | 8 records | 100.0%" in text
    assert "8 records hidden by pruning" in text
    assert "+--" not in text
    root = build_tree(pd.DataFrame({"record_id": ["a", "b"], "mutations": [[], []]}), 3, 1, 0)
    groups = group_assignments(root)
    assert groups.full_group_id.tolist() == [1, 1]
    assert groups.full_group_path.tolist() == ["Root", "Root"]
    assert groups.full_group_size.tolist() == [2, 2]


def test_dot_contains_exact_topology_and_escaped_labels(tmp_path, branching_tree):
    branching_tree.label = 'Root "quoted" \\ path <tag>'
    out = tmp_path / "tree.dot"
    write_dot_tree(out, branching_tree)
    dot = out.read_text()
    edges = {(int(a), int(b)) for a, b in re.findall(r"n(\d+) -> n(\d+);", dot)}
    assert len(edges) == 14
    assert edges == {(n.node_id, c.node_id) for n in iter_nodes(branching_tree) for c in (n.left, n.right) if c}
    labels = re.findall(r"n\d+ \[label=(.+)\];", dot)
    decoded = [json.loads(s) for s in labels]
    assert len(decoded) == 15
    assert branching_tree.label in decoded[0]
    assert all("records" in text for text in decoded)
    assert "branch length" not in dot


@pytest.mark.skipif(shutil.which("dot") is None, reason="Graphviz is required for native DOT rendering")
def test_native_graphviz_renders_editable_tree(tmp_path, branching_tree):
    dot = tmp_path / "tree.dot"
    svg = tmp_path / "tree.svg"
    write_dot_tree(dot, branching_tree)
    subprocess.run(["dot", "-Tsvg", str(dot), "-o", str(svg)], check=True, capture_output=True)
    root = ET.parse(svg)
    assert len(root.findall(".//{http://www.w3.org/2000/svg}g[@class='node']")) == 15
    assert len(root.findall(".//{http://www.w3.org/2000/svg}g[@class='edge']")) == 14


def test_new_exports_and_workbook_groups_agree(tmp_path, cfg, fasta):
    out = pipeline.run_one(cfg, fasta, tmp_path / "results")
    groups = pd.read_csv(out / "group_assignments.tsv", sep="\t").set_index("record_id")
    assert set(groups.index) == set("abcd")
    assert groups.loc["a", "full_group_path"] == "Root > Not F5Y"
    assert groups.loc["c", "full_group_path"] == "Root > F5Y"
    assert groups.full_group_size.tolist() == [2] * 4
    wb = load_workbook(out / "results.xlsx")
    values = list(wb["Records"].values)
    records = pd.DataFrame(values[1:], columns=values[0]).set_index("record_id")
    pd.testing.assert_frame_equal(records[groups.columns].sort_index(), groups.sort_index(), check_dtype=False)
    manifest = json.loads((out / "status.json").read_text())
    for name in ["tree_full.txt", "tree_pruned.txt", "tree_full.dot", "tree_pruned.dot", "group_assignments.tsv"]:
        assert manifest["artifacts"][name] > 0
    assert "full_group_id" in (out / "START_HERE.html").read_text()
