# FluTrees 0.3.1 validation scope

## Release identity and evidence

Version 0.3.1 supersedes 0.3.0 without changing its published tag or assets. The Test Kit records the source commit and successful CI run in `BUILD_INFO.txt`. Its `validation/` directory contains the JUnit test report, exact coverage counters, and the actual installer/alignment/performance measurements from that release build. Checksums cover the kit contents and separately published release assets.

## Legacy behavior and alternative views

Frequency-only runs with no alignment override retain the v0.2.3 alignment flags. Balanced, diversity, and all-mode runs default to reproducible refinement; explicit `--reproducible` and `--legacy-alignment` override the mode default. All views within an all-mode run share one alignment, reference, mutation table, and uncertainty mask.

Thirty frozen v0.2.3 tree hashes verify exact topology, membership, labels, node IDs, and stopping reasons for identical observations. Twelve end-to-end differential cases execute both current and pinned v0.2.3 code in separate processes using the same installed dependencies and real MAFFT. The four inputs cover the synthetic panel, public HA fixture, unknown/terminal-stop normalization, and short/duplicate records; current runs exercise default, explicit legacy, and explicit reproducible profiles. Assertions compare twelve scientific artifacts byte-for-byte, selected summary fields, and four workbook tables. Timestamps, software-version fields, and rendered-file metadata are not historical equality targets.

## Strategy and serialization acceptance

Five thousand Hypothesis-generated datasets exercise all three strategies against an independent position-level entropy and eligibility oracle. Cases include uncertainty masks, ties, rational frequency boundaries, record conservation, disjoint child partitions, depth limits, and non-mutating pruning. Each generated tree is serialized through JSON and reconstructed with the public reader; topology and reconstructed path-state sets must agree. Dedicated tests cover full and asymmetric pruned trees, stable reserialization, malformed data, duplicate IDs, invalid depth, membership mismatches, and corrupt JSON.

Diversity scoring excludes the candidate's whole residue position, counts categorical rather than one-hot allele entropy, and excludes incompletely observed sites consistently. A constructed fixture requires frequency, balanced, and diversity to select different root substitutions.

## Actual export boundaries

Oversized Excel tables continue on numbered sheets with repeated headers and filters. Tests cover multiple continuation sheets and the physical boundary of 1,048,576 worksheet rows, verifying every data row after reload. Overlong cell strings are rejected explicitly instead of silently truncated. Existing content, HTML escaping, formula protection, PDF pagination/geometry, SVG/DOT topology, Graphviz, GUI/Xvfb, interruption, and completion-gate tests remain required.

## Full HA pipeline performance

Release CI requires six complete runs: 100, 500, 1,000, 5,000, 10,000, and 25,000 full-length HA protein records. Inputs repeat the unmodified 24-record public fixture with distinct record IDs. The source file checksum, sequence lengths, repetition design, parameters, software versions, and hardware description are recorded. Repetition is a workload design, not evidence of 25,000 independent biological samples.

Each run invokes the installed candidate wheel through the real CLI with `--tree-mode all`. It does not stub alignment or suppress HTML, Excel, PDF, figures, or data exports. Profiling verifies exactly one alignment and three tree builds. Acceptance reloads the generated trees, assignments, and workbook XML, requiring complete record conservation and all declared artifacts. Measurements separate alignment, mutation calling, tree building, workbook, HTML, and figure/PDF costs. GNU time records elapsed/user/system time and maximum resident set size; the latter is the reported process maximum, not a sum of simultaneous process memory.

The six `measurement.json` files and CLI/resource logs are retained under `validation/acceptance/performance-<records>/` in the kit. They measure the actual release candidate on that environment, not a universal service-level guarantee. More divergent HA panels, deeper trees, and different hardware can be more expensive.

## Alignment profile comparison

Eighteen real MAFFT runs compare legacy and reproducible flags: 24, 100, and 500 HA observations, three repetitions per setting, and four threads. Execution order alternates. The record includes commands, alignment and mutation-observation hashes, median durations, and runtime ratios. Reproducible repetitions must agree for the fixture; any difference between legacy and reproducible outputs remains visible in the report. The evidence is `validation/acceptance/alignment/alignment-comparison.json`.

## Installation from the documented commands

Three isolated Linux jobs extract and execute the corresponding README bash block without rewriting its commands. venv builds from the candidate Git ref. Conda downloads and checksum-verifies the actual Anaconda Miniconda installer before execution. uv downloads and executes its pinned standalone installer. The installed wheel then generates all-mode results, checked for the candidate version and complete artifacts.

The documented `FLUTREES_REF` and `FLUTREES_PACKAGE` overrides select the candidate before public release; their values are recorded. They do not replace the bootstrap with a preinstalled tool. Transcripts, exact executed blocks, hashes, and outcome JSON are included under `validation/acceptance/installer-<method>/`.

## Boundaries

The matrix covers Linux with Python 3.9, 3.11, and 3.13. Native Windows/macOS desktop and bootstrap paths are not certified. Clinical, antigenic, phylogenetic, and standardized HA-numbering validity are not implied. Users must verify translation, shared input numbering, reference, residue window, and QC notes. No test count or coverage percentage proves absence of every possible defect. Forced termination, exhausted storage, or inputs exceeding practical memory capacity can still interrupt a run; only an explicit complete status indicates success.
