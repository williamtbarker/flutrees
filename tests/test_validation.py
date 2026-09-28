import os
import subprocess
from unittest.mock import Mock

import pandas as pd
import pytest
from Bio.Seq import Seq

from flutrees.config import RunConfig
from flutrees.io_fasta import load_fasta_extract_all, extract_region
from flutrees.mutations import call_mutations, choose_mode_reference, mutation_counts
from flutrees.tree_build import build_tree, prune_tree, to_dict, iter_nodes
from flutrees.align_mafft import check_mafft, mafft_align


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(start_residue=0),
        dict(start_residue=9, end_residue=8),
        dict(max_depth=-1),
        dict(max_depth=21),
        dict(min_split=0),
        dict(prune_cutoff=0),
        dict(min_freq=-0.1),
        dict(min_freq=0.6),
        dict(min_freq=float("nan")),
        dict(threads=0),
    ],
)
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        RunConfig(**kwargs)


def test_threads(monkeypatch):
    assert RunConfig.default_run_id().startswith("run")
    monkeypatch.delenv("SLURM_CPUS_PER_TASK", raising=False)
    assert RunConfig().resolved_threads() == 8
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "invalid")
    assert RunConfig().resolved_threads() == 8
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "4")
    assert RunConfig().resolved_threads() == 4
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "-5")
    assert RunConfig().resolved_threads() == 1
    assert RunConfig(threads=2).resolved_threads() == 2


def test_empty_invalid_and_out_of_window_fasta(tmp_path):
    p = tmp_path / "empty.fa"
    p.write_text("")
    with pytest.raises(ValueError, match="No FASTA"):
        load_fasta_extract_all(p, 1, 6)
    for value in [">a\n", ">a\nBAD123\n"]:
        p.write_text(value)
        with pytest.raises(ValueError, match="Invalid protein"):
            load_fasta_extract_all(p, 1, 6)
    p.write_text(">a\nACDE\n")
    with pytest.raises(ValueError, match="no residues"):
        load_fasta_extract_all(p, 20, 25)
    assert str(extract_region(Seq("AA"), 4, 5)) == "--"
    with pytest.raises(ValueError):
        extract_region(Seq("AA"), 2, 1)


def test_duplicate_ids_and_padding(tmp_path):
    p = tmp_path / "dups.fa"
    p.write_text(">a\nACD\n>a_2\nACDEF\n>a\nacdef\n>a\nACDEF\n")
    loaded = load_fasta_extract_all(p, 1, 5)
    assert loaded["metadata_df"].record_id.tolist() == ["a", "a_2", "a_3", "a_4"]
    assert loaded["metadata_df"].padded_residues.tolist() == [2, 0, 0, 0]
    assert str(loaded["extracted_records"][2].seq) == "ACDEF"


def test_numbering_missing_and_alignment_validation(tmp_path):
    p = tmp_path / "aligned.fa"
    p.write_text(">a\nAC-DE\n>b\nAC-DF\n>c\nAX-D-\n")
    df = call_mutations(p, "AC-DE", 84).set_index("record_id")
    assert df.loc["b", "mutations"] == ["E87F"]
    assert df.loc["c", "uncertain_positions"] == [85, 87]
    assert call_mutations(p, "AX-DE", 84).iloc[0].uncertain_positions == [85]
    p.write_text(">short\nAC\n")
    with pytest.raises(ValueError, match="length"):
        call_mutations(p, "ACDE", 1)
    with pytest.raises(ValueError, match="no residues"):
        call_mutations(p, "----", 1)
    p.write_text("")
    with pytest.raises(ValueError, match="empty"):
        call_mutations(p, "ACDE", 1)
    with pytest.raises(ValueError, match="No aligned"):
        choose_mode_reference(p)


def test_mode_ties_remain_input_order(tmp_path):
    p = tmp_path / "a.fa"
    p.write_text(">b\nACD\n>a\nACE\n>c\nACE\n>d\nACD\n")
    assert choose_mode_reference(p) == ("b", "ACD")
    empty = mutation_counts(pd.DataFrame({"record_id": ["a"], "mutations": [[]]}))
    assert empty.empty and list(empty) == ["mutations", "count"]


def test_tree_limits_frequency_missing_and_partition():
    df = pd.DataFrame(
        {"record_id": [str(i) for i in range(21)], "mutations": [["A1T"]] * 2 + [[]] * 19}
    )
    assert build_tree(df, 3, 1, 0.1).left is None
    with pytest.raises(ValueError):
        build_tree(pd.DataFrame(), 2, 1, 0)
    with pytest.raises(ValueError):
        build_tree(df.iloc[:0], 2, 1, 0)
    with pytest.raises(ValueError):
        build_tree(pd.concat([df, df]), 2, 1, 0)
    for depth, split, freq in [(-1, 1, 0), (21, 1, 0), (1, 0, 0), (1, 1, 1)]:
        with pytest.raises(ValueError):
            build_tree(df, depth, split, freq)
    # Globally present mutations cannot split; next candidates can.
    records = [["A1T", "C2D", "E3F"], ["A1T", "C2D"], ["A1T", "E3F"], ["A1T"], ["A1T"], ["A1T"]]
    data = pd.DataFrame({"record_id": list("abcdef"), "mutations": records})
    tree = build_tree(data, 4, 1, 0)
    assert tree.left and tree.right
    assert tree.left.seqs.isdisjoint(tree.right.seqs)
    assert tree.left.seqs | tree.right.seqs == tree.seqs
    assert tree.left.support + tree.right.support == 6
    assert to_dict(tree)["record_ids"] == list("abcdef")
    assert len(list(iter_nodes(tree))) > 3
    limited = build_tree(data, 0, 1, 0)
    assert limited.stop_reason == "Maximum depth reached."
    assert prune_tree(tree, 99).seqs == tree.seqs
    assert prune_tree(tree, 99).left is None
    with pytest.raises(ValueError):
        prune_tree(tree, 0)
    data["uncertain_positions"] = [[2, 3]] + [[]] * 5
    assert build_tree(data, 3, 1, 0).left is None
    data["mutations"] = [None] * 6
    assert build_tree(data, 3, 1, 0).left is None


def test_mafft_failure_and_environment(tmp_path, fake_mafft, fasta, monkeypatch):
    assert check_mafft(fake_mafft) == fake_mafft
    with pytest.raises(ValueError, match="not found"):
        check_mafft("no-such-mafft-executable-123")
    monkeypatch.setenv("SLURM_TMPDIR", str(tmp_path))
    monkeypatch.delenv("MAFFT_TMPDIR", raising=False)
    spy = Mock(return_value=subprocess.CompletedProcess([], 2))
    monkeypatch.setattr("flutrees.align_mafft.subprocess.run", spy)
    with pytest.raises(ValueError, match="exit 2"):
        mafft_align(fasta, tmp_path / "aligned.fa", fake_mafft, 2)
    assert spy.call_args.kwargs["env"]["MAFFT_TMPDIR"] == str(tmp_path)
    assert "MAFFT_TMPDIR" not in os.environ
    monkeypatch.setenv("MAFFT_TMPDIR", "keep-me")
    spy.return_value = subprocess.CompletedProcess([], 0)
    mafft_align(fasta, tmp_path / "aligned.fa", fake_mafft, 1)
    assert spy.call_args.kwargs["env"]["MAFFT_TMPDIR"] == "keep-me"
