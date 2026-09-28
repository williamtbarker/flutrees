"""These tests use the installed MAFFT binary, never a substituted aligner."""

import json
import shutil
from pathlib import Path

import pytest
from Bio import SeqIO
from typer.testing import CliRunner
from flutrees.cli import app


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("mafft") is None, reason="Real MAFFT is required")
def test_real_mafft_demo_through_cli(tmp_path):
    result = CliRunner().invoke(
        app, ["--demo", "--outdir", str(tmp_path), "--run-id", "real-mafft", "--threads", "1"]
    )
    assert result.exit_code == 0, result.output
    out = tmp_path / "real-mafft" / "example"
    assert json.loads((out / "status.json").read_text())["status"] == "complete"
    summary = json.loads((out / "summary.json").read_text())
    assert summary["n_records"] == 48
    assert sorted(x["count"] for x in summary["top_mutations"]) == [12, 12, 24]
    tree = json.loads((out / "tree_full.json").read_text())
    assert tree["support"] == 48
    assert tree["left"]["support"] == 24 and tree["right"]["support"] == 24
    records = list(SeqIO.parse(out / "aligned.fasta", "fasta"))
    assert len(records) == 48 and len({len(r.seq) for r in records}) == 1
    assert (out / "mafft.log").stat().st_size > 0


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("mafft") is None, reason="Real MAFFT is required")
def test_public_ha_against_independent_raw_sequence_oracle(tmp_path):
    import pandas as pd

    data = Path(__file__).parent / "data"
    expected = json.loads((data / "public_HA_expected.json").read_text())
    result = CliRunner().invoke(
        app,
        [
            "-i",
            str(data / "public_HA.fasta"),
            "-o",
            str(tmp_path),
            "--run-id",
            "public",
            "--threads",
            "1",
        ],
    )
    assert result.exit_code == 0, result.output
    out = tmp_path / "public" / "public_HA"
    summary = json.loads((out / "summary.json").read_text())
    assert (
        summary["reference_id"] == expected["reference"]
        and summary["n_records"] == expected["records"]
    )
    counts = pd.read_csv(out / "mutation_counts.tsv", sep="\t")
    assert dict(zip(counts.mutations, counts["count"])) == expected["counts"]
    tree = json.loads((out / "tree_full.json").read_text())

    def verify(node):
        assert len(node["record_ids"]) == node["support"]
        if node["left"]:
            left, right = node["left"], node["right"]
            assert set(left["record_ids"]).isdisjoint(right["record_ids"])
            assert set(left["record_ids"]) | set(right["record_ids"]) == set(node["record_ids"])
            verify(left)
            verify(right)

    verify(tree)
