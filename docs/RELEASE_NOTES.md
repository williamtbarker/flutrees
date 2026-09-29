# FluTrees 0.3.1

Completes the 0.3 release family's compatibility and acceptance checks while retaining its three complementary tree views. This patch supersedes 0.3.0; its published tag and assets remain unchanged.

## Download and start

Download `FluTrees_v0.3.1_Test_Kit.zip`, extract it, and open `START_HERE.html`. The kit contains the installable wheel, synthetic/public HA examples with all three views, complete installation instructions, and the actual validation evidence from this build. Python 3.9 or newer and MAFFT are required for new analyses; neither is bundled. Existing reports can be viewed without installing the software.

The wheel, source archive, example PDF, and release checksums are available separately. The README provides venv/pip, Anaconda Miniconda, and uv workflows, including the installer download commands.

## Changes

- Frequency-only runs now retain the historical MAFFT flags by default, in addition to the unchanged frequency split rule. Alternative/all modes default to reproducible refinement. Explicit `--reproducible` and `--legacy-alignment` override either default; all-mode trees still share one alignment.
- Exported full and pruned JSON trees can be reloaded with `flutrees.tree_io.read_tree`, with structural and record-membership validation and reconstructed path state.
- Oversized Excel tables continue on numbered worksheets. Cell strings exceeding the format limit fail with an explanation instead of being silently truncated.
- Release acceptance now includes 5,000 generated datasets across all modes, twelve differential CLI cases against pinned v0.2.3 source, JSON round trips, and the actual Excel worksheet row boundary.
- Six complete HA-input/real-MAFFT/all-view/report runs cover 100 through 25,000 records, with conservation checks, stage timings, and resource records. Eighteen repeated alignment runs quantify legacy/reproducible behavior and cost.
- Separate isolated jobs execute the actual README venv, curl/Miniconda, and curl/uv command blocks. Their transcripts, hashes, and completed example records are included in the kit.

Frequency, balanced, diversity, and `--tree-mode all` remain available through the CLI and desktop window. Existing reference selection, input integrity, portable names, provenance, comparisons, and completion protections remain in place.

## Release gates and interpretation

Publication requires the Linux Python 3.9/3.11/3.13 tests with exact 100% application statement and branch coverage, real MAFFT, desktop/Xvfb, Chromium, Graphviz, clean-wheel examples, all installation checks, all six pipeline sizes, alignment comparisons, and verified packaging. No coverage exclusions or reduced thresholds were introduced.

The large workload repeats unmodified public HA records with unique IDs; it is not 25,000 independent biological samples. Tests establish the specified behavior under tested environments, not clinical validity, phylogeny, standardized HA numbering, universal capacity, or equivalence across different dependencies. Native Windows/macOS desktop installation remains outside the Linux matrix. See `docs/ACCEPTANCE.md` and `docs/VALIDATION_0.3.1.md` for the exact contracts.
