"""Independent split oracles, legacy golden hashes, and shrinking property tests."""

import hashlib
import json
import math
import random
from collections import Counter
from fractions import Fraction
from pathlib import Path

import pandas as pd
from hypothesis import given, settings, strategies as st

from flutrees.tree_io import from_dict
from flutrees.strategies import SplitSelector, entropy
from flutrees.tree_build import build_tree, iter_nodes, prune_tree, to_dict

MODES = ("frequency", "balanced", "diversity")


def observations_frame(observations):
    return pd.DataFrame([
        {"record_id": str(i),
         "mutations": [f"A{j + 1}{aa}" for j, aa in enumerate(seq) if aa in "TG"],
         "uncertain_positions": [j + 1 for j, aa in enumerate(seq) if aa == "X"]}
        for i, seq in enumerate(observations)
    ])


def digest(tree):
    return hashlib.sha256(json.dumps(to_dict(tree), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def test_frequency_matches_frozen_023_tree_hashes():
    fixture = json.loads((Path(__file__).parent / "data/frequency_023_golden.json").read_text())
    for case in fixture["cases"]:
        seed = case["seed"]
        rng = random.Random(seed)
        n = rng.randint(4, 50)
        observations = [[rng.choice("AATG" + ("X" if seed % 3 == 0 else "")) for _ in range(5)] for _ in range(n)]
        frame = observations_frame(observations)
        for kwargs in ({}, {"strategy": "frequency"}):
            assert digest(build_tree(frame, **case["settings"], **kwargs)) == case["tree_sha256"]


def test_three_distinct_views_on_one_population():
    observations = [
        ["T" if i < 16 else "A", "T" if i % 2 == 0 else "A"] + ["T" if i < 6 else "A"] * 4
        for i in range(20)
    ]
    frame = observations_frame(observations)
    assert [build_tree(frame, 4, 1, 0, mode).left.label for mode in MODES] == ["A1T", "A2T", "A3T"]


def independent_entropy(values):
    counts = Counter(values)
    return sum(-count / len(values) * math.log2(count / len(values)) for count in counts.values())


def independent_choice(observations, node, minimum, frequency, mode, encounter):
    ids = sorted(map(int, node.seqs))
    n = len(ids)
    candidates = []
    for mutation in encounter:
        pos, aa = int(mutation[1:-1]) - 1, mutation[-1]
        if mutation in node.used or any(observations[i][pos] == "X" for i in ids):
            continue
        positive = [i for i in ids if observations[i][pos] == aa]
        negative = [i for i in ids if observations[i][pos] != aa]
        w = len(positive)
        if min(w, n - w) < minimum or Fraction(min(w, n - w), n) < Fraction(str(frequency)):
            continue
        if mode == "frequency":
            score = (w,)
        elif mode == "balanced":
            score = (min(w, n - w), w)
        else:
            gain = 0.0
            for other in range(len(observations[0])):
                if other == pos or any(observations[i][other] == "X" for i in ids):
                    continue
                before = independent_entropy([observations[i][other] for i in ids])
                after = (w * independent_entropy([observations[i][other] for i in positive])
                         + (n - w) * independent_entropy([observations[i][other] for i in negative])) / n
                gain += before - after
            score = (round(max(0, gain), 12), min(w, n - w), w)
        candidates.append((score, mutation))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


@settings(max_examples=5000, deadline=None, derandomize=True)
@given(st.one_of(
    st.lists(st.lists(st.sampled_from(list("AATG")), min_size=5, max_size=5), min_size=2, max_size=40),
    st.lists(st.lists(st.sampled_from(list("AATGX")), min_size=5, max_size=5), min_size=2, max_size=40)),
       st.integers(0, 5), st.integers(1, 3), st.sampled_from([0, 0.07, 0.1, 0.5]))
def test_all_modes_against_independent_position_oracle(observations, depth, minimum, frequency):
    frame = observations_frame(observations)
    encounter = list(dict.fromkeys(m for row in frame.mutations for m in row))
    for mode in MODES:
        tree = build_tree(frame, depth, minimum, frequency, mode)
        assert digest(tree) == digest(build_tree(frame, depth, minimum, frequency, mode))
        restored = from_dict(json.loads(json.dumps(to_dict(tree))))
        assert digest(restored) == digest(tree)
        assert [n.used for n in iter_nodes(restored)] == [n.used for n in iter_nodes(tree)]
        leaves = []
        for node in iter_nodes(tree):
            assert node.depth <= depth and node.support == len(node.seqs)
            chosen = None if node.depth == depth else independent_choice(
                observations, node, minimum, frequency, mode, encounter)
            assert (node.left.label if node.left else None) == chosen
            if node.left is None:
                leaves.extend(node.seqs)
                continue
            left, right = node.left, node.right
            assert left.seqs.isdisjoint(right.seqs) and left.seqs | right.seqs == node.seqs
            pos, aa = int(chosen[1:-1]) - 1, chosen[-1]
            assert all(observations[int(r)][pos] != "X" for r in node.seqs)
            assert left.seqs == {r for r in node.seqs if observations[int(r)][pos] == aa}
            assert min(left.support, right.support) >= minimum
            assert Fraction(min(left.support, right.support), node.support) >= Fraction(str(frequency))
        assert sorted(leaves) == sorted(frame.record_id)
        before = digest(tree)
        assert prune_tree(tree, 3).seqs == tree.seqs
        assert digest(tree) == before


def test_entropy_zero_gain_and_unknown_features():
    assert entropy([]) == 0 and entropy([0, 0]) == 0
    assert entropy([1, 1, 0]) == 1 and entropy([7]) == 0
    selector = SplitSelector({"A1T": {"a"}, "A2T": {"a", "b"}}, {2: {"a"}}, 1, 0, "diversity")
    assert selector.choose({"a", "b"}, set()) == "A1T"
    assert selector.diversity_scores({"a", "b"}, [("A1T", {"a"})]) == {"A1T": 0.0}
    assert SplitSelector({}, {}, 1, 0, "diversity").choose({"a"}, set()) is None
