import pandas as pd
from flutrees.tree_build import build_tree, prune_tree, to_dict


def test_tree_builds_and_serializes():
    df = pd.DataFrame({
        "record_id": ["a", "b", "c", "d", "e", "f"],
        "mutations": [["A1T"], ["A1T"], ["A1T"], [], [], []],
    })
    root = build_tree(df, max_depth=3, min_split=2, min_freq=0.1)
    assert root.support == 6
    assert root.left is not None
    assert root.right is not None
    d = to_dict(prune_tree(root, 2))
    assert d["support"] == 6
