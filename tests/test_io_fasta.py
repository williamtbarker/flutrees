from Bio.Seq import Seq
from flutrees.io_fasta import extract_region


def test_extract_region_exact_window():
    assert str(extract_region(Seq("ABCDEFGHIJ"), 3, 6)) == "CDEF"


def test_extract_region_pads_short_sequence():
    assert str(extract_region(Seq("ABCDE"), 4, 8)) == "DE---"
