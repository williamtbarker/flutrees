"""Measure split construction separately from alignment and reporting."""

import argparse
import json
import platform
import random
import time
from pathlib import Path

import pandas as pd

from flutrees import __version__
from flutrees.tree_build import build_tree, iter_nodes


def benchmark(sizes):
    results = []
    for n in sizes:
        rng = random.Random(20260929)
        data = pd.DataFrame({
            "record_id": [str(i) for i in range(n)],
            "mutations": [[f"A{j+1}T" for j in range(12) if rng.random() < (0.2 + j * 0.04)] for _ in range(n)],
        })
        for mode in ("frequency", "balanced", "diversity"):
            start = time.perf_counter()
            tree = build_tree(data, 6, 5, 0.05, mode)
            results.append({"records": n, "mode": mode, "seconds": round(time.perf_counter() - start, 6),
                            "nodes": len(list(iter_nodes(tree)))})
    return {"version": __version__, "python": platform.python_version(), "platform": platform.platform(),
            "scope": "Tree construction only: 12 synthetic binary sites; depth 6; min_split 5; min_freq 0.05; no unknowns. Excludes MAFFT and exports.",
            "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[100, 500, 1000, 5000, 10000, 25000])
    parser.add_argument("--output", type=Path, default=Path("benchmark.json"))
    args = parser.parse_args()
    if any(n < 1 for n in args.sizes):
        parser.error("sizes must be positive")
    args.output.write_text(json.dumps(benchmark(args.sizes), indent=2) + "\n", encoding="utf-8")
    print(f"Benchmark saved to {args.output.resolve()}")


if __name__ == "__main__":
    main()
