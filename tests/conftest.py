import sys
import pytest
from flutrees.config import RunConfig


@pytest.fixture
def fake_mafft(tmp_path):
    path = tmp_path / "fake_mafft"
    path.write_text(
        f'#!{sys.executable}\nimport pathlib,sys\nprint(pathlib.Path(sys.argv[-1]).read_text(),end="")\n'
    )
    path.chmod(0o755)
    return str(path)


@pytest.fixture
def cfg(fake_mafft):
    return RunConfig(
        mafft=fake_mafft,
        threads=1,
        start_residue=1,
        end_residue=6,
        max_depth=3,
        min_split=1,
        min_freq=0.05,
        prune_cutoff=1,
    )


@pytest.fixture
def fasta(tmp_path):
    p = tmp_path / "sample.fasta"
    p.write_text(">a\nACDEFG\n>b\nACDEFG\n>c\nACDEYG\n>d\nACDEYG\n")
    return p
