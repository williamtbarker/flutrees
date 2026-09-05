from pathlib import Path

from flutrees.config import RunConfig
from flutrees.pipeline import run_one


def test_pipeline_smoke_with_passthrough_mafft(tmp_path: Path):
    fasta = tmp_path / "input.fasta"
    fasta.write_text(
        ">a\nAAAAAA\n>b\nAAAAAA\n>c\nAATAAA\n>d\nAATAAA\n",
        encoding="utf-8",
    )

    mafft = tmp_path / "fake_mafft"
    mafft.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        "print(pathlib.Path(sys.argv[-1]).read_text(), end='')\n",
        encoding="utf-8",
    )
    mafft.chmod(0o755)

    cfg = RunConfig(
        mafft=str(mafft),
        threads=1,
        start_residue=1,
        end_residue=6,
        max_depth=2,
        min_split=1,
        min_freq=0.1,
        prune_cutoff=1,
    )
    run_root = tmp_path / "runs"
    run_one(cfg, fasta, run_root)

    out = run_root / "input"
    expected = {
        "aligned.fasta",
        "extracted.fasta",
        "metadata.tsv",
        "mutation_counts.tsv",
        "mutations_per_record.tsv",
        "node_summary.tsv",
        "report.pdf",
        "run_info.txt",
        "summary.json",
        "tree_full.json",
        "tree_pruned.json",
    }
    assert expected.issubset({p.name for p in out.iterdir()})
