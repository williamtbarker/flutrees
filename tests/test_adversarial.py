"""Regressions from deliberately hostile and scientifically misleading inputs."""

import json
import hashlib
import random
import shutil
from dataclasses import replace
from fractions import Fraction
from unittest.mock import Mock

import pandas as pd
import pytest
from Bio import SeqIO
from openpyxl import load_workbook
from typer.testing import CliRunner
from xlsxwriter.exceptions import FileCreateError

from flutrees import pipeline
from flutrees.cli import app
from flutrees.io_fasta import load_fasta_extract_all
from flutrees.tree_build import build_tree, iter_nodes, prune_tree


@pytest.mark.parametrize(
    "body, message",
    [
        (">\nACDEFG\n", "nonempty ID"),
        (">a\nAC-DEFG\n", "alignment gaps"),
        (">a\nAC*DEFG\n", "internal stop"),
        (">a\nACDEFG**\n", "internal stop"),
        (">a\nXXXXXX\n", "no residues"),
        (">a\n??????\n", "no residues"),
        (">a\n*\n", "no residues"),
    ],
)
def test_uninterpretable_inputs_fail_before_creating_results(tmp_path, cfg, body, message):
    fasta = tmp_path / "bad.fasta"
    fasta.write_text(body)
    with pytest.raises(ValueError, match=message):
        pipeline.run_many(cfg, [fasta], tmp_path / "results", "bad")
    assert not (tmp_path / "results").exists()


def test_unknown_normalization_preserves_length_and_terminal_stop_is_not_a_residue(tmp_path):
    fasta = tmp_path / "unknown.fasta"
    fasta.write_text(">a\nAC?UOBZJ*\n")
    loaded = load_fasta_extract_all(fasta, 1, 10)
    assert str(loaded["extracted_records"][0].seq) == "ACXXXBZJ--"
    meta = loaded["metadata_df"].iloc[0]
    assert meta.normalized_residues == 3
    assert meta.terminal_stop_removed and meta.input_length == 8 and meta.padded_residues == 2


@pytest.mark.parametrize("change", ["remove", "replace", "duplicate_id", "unequal_length"])
def test_corrupt_aligner_output_is_never_published(tmp_path, cfg, fasta, monkeypatch, change):
    def corrupt(source, destination, *_):
        records = list(SeqIO.parse(source, "fasta"))
        if change == "remove":
            records[0].seq = records[0].seq[1:]
        elif change == "replace":
            records[0].seq = records[0].seq.replace("A", "G")
        elif change == "duplicate_id":
            records[1].id = records[0].id
        else:
            records[0].seq += "-"
        SeqIO.write(records, destination, "fasta")

    monkeypatch.setattr(pipeline, "mafft_align", corrupt)
    message = "IDs" if change == "duplicate_id" else "length" if change == "unequal_length" else "residues"
    with pytest.raises(ValueError, match=message):
        pipeline.run_many(cfg, [fasta], tmp_path / "results", "corrupt")
    root = tmp_path / "results" / "corrupt"
    assert json.loads((root / "status.json").read_text())["status"] == "failed"
    assert json.loads((root / "sample" / "status.json").read_text())["status"] == "failed"
    assert not (root / "START_HERE.html").exists()


def test_reordered_aligner_output_preserves_reference_tie_break(tmp_path, cfg, fasta, monkeypatch):
    original_bytes = fasta.read_bytes()

    def reverse(source, destination, *_):
        records = list(SeqIO.parse(source, "fasta"))[::-1]
        SeqIO.write(records, destination, "fasta")
        # Simulate a user editing the original file while alignment is running.
        fasta.write_text(">changed\nYYYYYY\n")

    monkeypatch.setattr(pipeline, "mafft_align", reverse)
    out = pipeline.run_one(cfg, fasta, tmp_path / "results")
    assert json.loads((out / "summary.json").read_text())["reference_id"] == "a"
    assert [rec.id for rec in SeqIO.parse(out / "aligned.fasta", "fasta")] == list("abcd")
    assert (out / "input.fasta").read_bytes() == original_bytes
    assert json.loads((out / "summary.json").read_text())["input_sha256"] == hashlib.sha256(original_bytes).hexdigest()


def test_visual_export_omission_and_interrupt_cannot_report_success(tmp_path, cfg, fasta, monkeypatch):
    original = pipeline._analyze

    def lose_png(*args):
        original(*args)
        (args[2] / "tree_pruned.png").unlink()

    monkeypatch.setattr(pipeline, "_analyze", lose_png)
    with pytest.raises(ValueError, match="missing or empty"):
        pipeline.run_many(cfg, [fasta], tmp_path, "missing-image")
    assert json.loads((tmp_path / "missing-image" / "sample" / "status.json").read_text())["status"] == "failed"
    monkeypatch.setattr(pipeline, "_analyze", Mock(side_effect=KeyboardInterrupt))
    with pytest.raises(KeyboardInterrupt):
        pipeline.run_many(cfg, [fasta], tmp_path, "cancelled")
    for folder in [tmp_path / "cancelled", tmp_path / "cancelled" / "sample"]:
        status = json.loads((folder / "status.json").read_text())
        assert status["status"] == "failed" and "interrupted" in status["error"]


def test_workbook_file_error_is_actionable_in_cli(tmp_path, fasta, monkeypatch):
    monkeypatch.setattr(pipeline, "run_many", Mock(side_effect=FileCreateError("Workbook is locked")))
    result = CliRunner().invoke(app, ["-i", str(fasta), "-o", str(tmp_path)])
    assert result.exit_code == 1
    assert "Could not complete analysis: Workbook is locked" in result.output


def test_exact_decimal_frequency_boundary():
    data = pd.DataFrame({"record_id": list(map(str, range(100))), "mutations": [["A1T"]] * 7 + [[]] * 93})
    tree = build_tree(data, 1, 1, 0.07)
    assert tree.left.support == 7 and tree.right.support == 93
    pruned = prune_tree(tree, 8)
    assert pruned.left is None and pruned.right.support == 93
    assert "7 records hidden by pruning" in pruned.stop_reason
    assert tree.stop_reason == ""  # pruning must not mutate the full tree


def test_randomized_tree_partitions_against_independent_observation_oracle():
    rng = random.Random(20260928)
    tested_splits = 0
    for trial in range(100):
        n = rng.randint(2, 80)
        alphabet = ["A", "A", "T", "G", "X"] if trial % 3 == 0 else ["A", "T", "G"]
        observations = {str(i): [rng.choice(alphabet) for _ in range(5)] for i in range(n)}
        data = pd.DataFrame([
            {"record_id": rid,
             "mutations": [f"A{j + 1}{aa}" for j, aa in enumerate(seq) if aa in {"T", "G"}],
             "uncertain_positions": [j + 1 for j, aa in enumerate(seq) if aa == "X"]}
            for rid, seq in observations.items()
        ])
        depth, minimum, freq = rng.randint(0, 6), rng.randint(1, 4), rng.choice([0, 0.07, 0.1, 0.5])
        tree = build_tree(data, depth, minimum, freq)
        leaves = []
        for node in iter_nodes(tree):
            assert node.support == len(node.seqs) and node.depth <= depth
            if node.left is None:
                leaves.extend(node.seqs)
                continue
            left, right = node.left, node.right
            tested_splits += 1
            position, residue = int(left.label[1:-1]) - 1, left.label[-1]
            assert all(observations[r][position] != "X" for r in node.seqs)
            assert left.seqs == {r for r in node.seqs if observations[r][position] == residue}
            assert right.seqs == node.seqs - left.seqs
            for child in [left, right]:
                assert child.support >= minimum
                assert Fraction(child.support, node.support) >= Fraction(str(freq))
        assert sorted(leaves) == sorted(observations)
    assert tested_splits > 100


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("mafft") is None, reason="Real MAFFT is required")
def test_real_mafft_preserves_unknown_coordinates_and_long_ids(tmp_path, cfg):
    long_id = "reference_" + "a" * 500
    fasta = tmp_path / "adversarial.fasta"
    fasta.write_text(f">{long_id}\nAC?DEFGHIKLMNPQ*\n>same\nAC?DEFGHIKLMNPQ*\n>variant\nAC?DEYGHIKLMNPQ*\n")
    out = pipeline.run_one(replace(cfg, mafft="mafft", end_residue=15), fasta, tmp_path / "results")
    summary = json.loads((out / "summary.json").read_text())
    assert summary["reference_id"] == long_id
    counts = pd.read_csv(out / "mutation_counts.tsv", sep="\t")
    assert dict(zip(counts.mutations, counts["count"])) == {"F6Y": 1}
    mutations = pd.read_csv(out / "mutations_per_record.tsv", sep="\t", dtype=str)
    assert mutations.uncertain_positions.tolist() == ["3", "3", "3"]
    assert mutations.record_id.tolist() == [long_id, "same", "variant"]
    warnings = " ".join(summary["warnings"])
    assert "preserved as X" in warnings and "Terminal stop" in warnings
    assert load_workbook(out / "results.xlsx")["Records"]["A2"].value == long_id
    # A common short reference must explicitly disclose its smaller comparable window.
    fasta.write_text(">short1\nACDEF\n>short2\nACDEF\n>long\nACDEFGHIKLMNPQ\n")
    out = pipeline.run_one(replace(cfg, mafft="mafft", end_residue=14), fasta, tmp_path / "short-reference")
    assert "reference is shorter" in " ".join(json.loads((out / "summary.json").read_text())["warnings"])
