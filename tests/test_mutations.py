from pathlib import Path
from flutrees.mutations import choose_mode_reference, call_mutations


def test_mode_reference_and_calls(tmp_path: Path):
    p = tmp_path / "a.fa"
    p.write_text(">a\nAAAA\n>b\nAAAA\n>c\nAATA\n")
    rid, seq = choose_mode_reference(p)
    assert rid == "a"
    assert seq == "AAAA"
    df = call_mutations(p, seq, 1)
    muts = dict(zip(df.record_id, df.mutations))
    assert muts["a"] == []
    assert muts["c"] == ["A3T"]
