from flutrees.metadata import parse_header_robust


def test_parse_header_never_throws_on_empty():
    d = parse_header_robust("")
    assert d["strain"] == "Unknown"
    assert d["raw_header"] == ""


def test_parse_legacy_header():
    d = parse_header_robust("H3N2|A/NewYork/1/2025|EPI123|HA|complete")
    assert d["type_subtype"] == "H3N2"
    assert d["gisaid_id"] == "EPI123"
    assert d["gene_segment"] == "HA"
