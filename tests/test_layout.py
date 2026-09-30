"""Adversarial configuration, label-fit, viewport, and presentation invariants."""

import json
from dataclasses import replace

import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st
from pypdf import PdfReader

from flutrees.config import RunConfig
from flutrees.layout import FigureStyle, FIGURE_FIELDS, image_size
from flutrees.figures import tree_figure, tree_pages
from flutrees.pipeline import run_one
from flutrees.provenance import validate_run_id
from flutrees.tree_build import build_tree, prune_tree, iter_nodes


@pytest.mark.parametrize("name", ["start_residue", "end_residue", "max_depth", "min_split", "prune_cutoff", "threads"])
@pytest.mark.parametrize("value", [True, 2.5, "2", float("nan")])
def test_config_requires_exact_integer_types(name, value):
    with pytest.raises(ValueError, match="integer"):
        RunConfig(**{name: value})


@pytest.mark.parametrize("name,value", [
    ("mafft", None), ("mafft", ""), ("mafft", "a\x00b"), ("tree_mode", []),
    ("reference_id", 12), ("reference_id", ""), ("min_freq", True), ("min_freq", "0.1"),
    ("min_freq", 10**500), ("min_freq", float("inf")),
])
def test_invalid_boundary_types_raise_actionable_value_errors(name, value):
    with pytest.raises(ValueError):
        RunConfig(**{name: value})


@pytest.mark.parametrize("value", [None, [], True, 12])
def test_run_name_types(value):
    with pytest.raises(ValueError, match="Run ID"):
        validate_run_id(value)


@pytest.mark.parametrize("name", FIGURE_FIELDS)
@pytest.mark.parametrize("value", [True, "1", float("nan"), float("inf"), -1, 10**500])
def test_layout_rejects_invalid_values(name, value):
    with pytest.raises(ValueError, match="finite number"):
        FigureStyle(**{name: value})
    with pytest.raises(ValueError, match="finite number"):
        RunConfig(**{name: value})


def test_direct_tree_api_rejects_wrong_types():
    data = pd.DataFrame({"record_id": ["a", "b"], "mutations": [[], ["A1T"]]})
    for depth, count, freq in [(True, 1, 0), (1.5, 1, 0), (2, True, 0), (2, 1.5, 0),
                               (2, 1, True), (2, 1, "0.1")]:
        with pytest.raises(ValueError, match="Invalid tree settings"):
            build_tree(data, depth, count, freq)
    tree = build_tree(data, 2, 1, 0)
    for cutoff in (True, 1.5, "1"):
        with pytest.raises(ValueError, match="Pruning cutoff"):
            prune_tree(tree, cutoff)


def branching_tree(bits=5):
    data = pd.DataFrame({"record_id": [str(i) for i in range(2**bits)],
                         "mutations": [[f"A{b + 1}T" for b in range(bits) if i & (1 << b)]
                                       for i in range(2**bits)]})
    return build_tree(data, bits, 1, 0)


@pytest.mark.parametrize("width,height", [(6, 4), (6, 24), (30, 4), (30, 24), (14, 8.5)])
@pytest.mark.parametrize("gap", [0.25, 4.0])
def test_measured_node_boxes_fit_and_do_not_overlap_at_layout_extremes(width, height, gap):
    tree = branching_tree()
    pages = tree_pages(tree)
    mapping = {page[0].node_id: i for i, page in enumerate(pages, 1)}
    style = FigureStyle(width, height, gap, gap, 5)
    for page_number in (1, len(pages)):
        fig = tree_figure(pages[page_number - 1], tree.support, "Diversity: Pruned mutation decision tree",
                          page_number, mapping, style)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        boxes = [text.get_bbox_patch().get_window_extent(renderer) for text in fig.axes[0].texts]
        for i, box in enumerate(boxes):
            assert fig.bbox.contains(box.x0, box.y0) and fig.bbox.contains(box.x1, box.y1)
            assert all(not box.overlaps(other) for other in boxes[i + 1:])
        for text in fig.texts:
            box = text.get_window_extent(renderer)
            assert fig.bbox.contains(box.x0, box.y0) and fig.bbox.contains(box.x1, box.y1)
        assert tuple(fig.get_size_inches()) == (width, height)


def test_deep_and_asymmetric_trees_keep_all_nodes_across_bounded_pages():
    from flutrees.tree_build import Node

    tree = Node(1, 0, "Root", 21, set(map(str, range(21))), set())
    node = tree
    # A valid comb reaches the maximum depth with unequal branching.
    for depth in range(1, 21):
        left_ids = set(map(str, range(depth, 21)))
        node.left = Node(2 * depth, depth, f"A{depth}T", len(left_ids), left_ids, set())
        node.right = Node(2 * depth + 1, depth, f"Not A{depth}T", 1, {str(depth - 1)}, set())
        node = node.left
    for candidate in (tree, prune_tree(tree, 2), Node(1, 0, "Root", 1, {"a"}, set())):
        pages = tree_pages(candidate)
        assert max(map(len, pages)) <= 15
        assert {n.node_id for p in pages for n in p} == {n.node_id for n in iter_nodes(candidate)}
        mapping = {p[0].node_id: i for i, p in enumerate(pages, 1)}
        fig = tree_figure(pages[-1], candidate.support, "Deep tree", len(pages), mapping)
        fig.canvas.draw()
        assert all(fig.bbox.contains(*fig.axes[0].transData.transform(t.get_position())) for t in fig.axes[0].texts)


@given(width=st.integers(1, 1_000_000), height=st.integers(1, 1_000_000),
       vw=st.integers(1, 10000), vh=st.integers(1, 10000), zoom=st.floats(0.25, 8))
@settings(max_examples=250, deadline=None)
def test_viewport_always_bounds_pixel_allocation(width, height, vw, vh, zoom):
    w, h = image_size(width, height, vw, vh, zoom)
    assert 1 <= w <= 8000 and 1 <= h <= 8000 and w * h <= 8_000_000
    w, h = image_size(width, height, vw, vh)
    assert w <= vw and h <= vh


@pytest.mark.parametrize("args", [(0, 1, 1, 1), (True, 1, 1, 1), (1, "2", 3, 4), (10**500, 1, 1, 1), (1, 1, 1, 1, float("nan"))])
def test_viewport_rejects_invalid_dimensions(args):
    with pytest.raises(ValueError):
        image_size(*args)


def test_layout_changes_exports_but_not_science_or_analytical_identity(tmp_path, cfg, fasta):
    first = run_one(replace(cfg, tree_mode="all"), fasta, tmp_path / "default")
    styled = run_one(replace(cfg, tree_mode="all", figure_width=9, figure_height=12,
                             level_spacing=2, node_spacing=3, line_width=2.5), fasta, tmp_path / "styled")
    before = json.loads((first / "provenance.json").read_text())
    after = json.loads((styled / "provenance.json").read_text())
    assert before["analysis_id"] == after["analysis_id"]
    for mode in ("frequency", "balanced", "diversity"):
        for name in ("tree_full.json", "tree_pruned.json", "group_assignments.tsv"):
            assert (first / "trees" / mode / name).read_bytes() == (styled / "trees" / mode / name).read_bytes()
        page = PdfReader(styled / "trees" / mode / "tree_full.pdf").pages[0]
        assert float(page.mediabox.width) == 9 * 72 and float(page.mediabox.height) == 12 * 72
    assert (first / "tree_full.png").read_bytes() != (styled / "tree_full.png").read_bytes()
    report_page = PdfReader(styled / "report.pdf").pages[-1]
    assert float(report_page.mediabox.width) == 9 * 72
    summary = json.loads((styled / "summary.json").read_text())
    assert summary["config"]["figure_height"] == 12
