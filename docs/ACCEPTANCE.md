# Release acceptance requirements

The 0.3 release family is published only after the following technical checks succeed. The release workflow preserves previous tags and assets rather than replacing an existing version.

| Requirement | Executable acceptance | Evidence |
|---|---|---|
| Legacy frequency semantics and default invocation | 30 frozen v0.2.3 tree cases; 12 real CLI differential cases against hashed historical source | `tests/test_strategies.py`, `tests/test_legacy_end_to_end.py`, JUnit report |
| Distinct balanced and diversity alternatives | Independent scoring oracle; fixture with three different root decisions | `tests/test_strategies.py` |
| Shared alignment and complete results family | One alignment, shared observations/provenance, three mode exports, per-record group conservation | `tests/test_family.py`; full-pipeline measurements |
| Deterministic decisions and uncertainty protections | 5,000 generated cases across all modes; exact count/frequency and partition invariants | Property suite and JUnit report |
| JSON serialization and reloading | Validated reader; full/pruned round trips; malformed data rejection | `tests/test_tree_io.py` and property suite |
| Reproducibility and legacy alignment options | Effective profile recorded; exact flags checked; 18 timed real-MAFFT comparisons | `tests/test_family.py`; `validation/acceptance/alignment/` |
| Versions, commands, hashes, reference selection | Provenance/fingerprint and explicit-reference regressions | `tests/test_family.py` and example `provenance.json` |
| Portable paths, complete exports, interruption safety | Filename collisions, missing continuation artifacts, failed writes and interrupts | Existing adversarial, result, family, and validation tests |
| Large output format integrity | Actual Excel row boundary; continued sheets; overlong cells fail visibly | `tests/test_large_exports.py` |
| Complete HA pipeline at six dataset sizes | Real alignment and all exports at 100, 500, 1,000, 5,000, 10,000, 25,000 records; independent output conservation checks | `validation/acceptance/performance-*/` |
| Complete README and three installation paths | Verbatim venv, actual curl/Miniconda, actual curl/uv blocks, installed-wheel analyses | `validation/acceptance/installer-*/` |
| Existing test and coverage requirements | Linux Python 3.9/3.11/3.13/3.14, zero missing statements/branches, zero excluded lines | `validation/coverage-python311.json`, JUnit report, CI jobs |
| Visual/desktop/browser portability | PDF/SVG/PNG/DOT/XLSX content, Graphviz, Xvfb desktop, Chromium | Test and browser jobs |
| Versioned customer package | Checked wheel/source, examples, instructions, all acceptance evidence, internal/external checksums | Test Kit, source archive, wheel, `BUILD_INFO.txt`, `SHA256SUMS.txt` |

The full workload repeats unmodified public HA fixture records with unique identifiers; it does not claim a representative 25,000-isolate surveillance panel. See `VALIDATION_0.3.1.md` for the exact workload, equality contract, and interpretation boundaries.
