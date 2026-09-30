# Changelog

## 0.3.2 - 2026-09-30

- Add a step-by-step GUI quickstart and Test Kit walkthrough; separate application prerequisites from optional renderer and release tooling in maintainer setup.
- Expose every existing analysis setting in the desktop, including Max depth, Min split, Min freq, Run ID, Prune cutoff, CPU threads, alignment profile, and MAFFT executable.
- Organize the native GUI into Analysis, Advanced, Tree viewer, and Run log tabs with file add/remove/clear controls, full input locations, fixed action/status controls, and scrollable analysis settings.
- Add quoted, copyable CLI commands and a session progress log. Lock configuration during execution and restore controls after completion or failure.
- Validate numeric settings and portable run names before launching; preserve existing results when a chosen folder already exists. Reuse pipeline run-name validation.
- Clarify fractional frequency, per-child eligibility, depth limits, and presentation-only pruning. Document full GUI/CLI parity and fixed scientific policies.
- Extend GUI/CLI parameter, native desktop, command-quoting, failure-recovery, and output-equivalence tests. Preserve scientific algorithms, defaults, existing CLI flags, scientific data schemas, and existing release gates.

- Add optional width/height, level/node gap, and branch-width controls to GUI/CLI, with one measured renderer for previews and tree figures. Record presentation settings without changing analytical identity.
- Add completed-run loading, page navigation, fitted zoom/pan, and single-page PNG/SVG/PDF export. Bound preview inputs and raster allocation; preserve continuation pages.
- Fix clipboard and worker-start recovery, stale previews after invalid layout, pending Tk callbacks, and repeated-window cleanup before background work. Strengthen runtime numeric types and add static checking plus Python 3.14 CI coverage.
- Document adversarial review, layout invariants, and Python/MAFFT dependency servicing.

## 0.3.1 - 2026-09-29

- Restore the historical alignment flag set for default frequency-only runs; use reproducible refinement by default for alternative/all views and record the effective override.
- Add validated JSON tree loading, reconstructed path state, and full/pruned round-trip acceptance.
- Continue oversized Excel tables across numbered sheets and explicitly reject cell values that Excel would truncate.
- Expand strategy property tests to 5,000 datasets, add twelve end-to-end comparisons against immutable v0.2.3 source, and exercise the physical Excel row boundary.
- Gate releases on six complete HA alignment/report workloads through 25,000 records, eighteen repeated alignment-profile measurements, and verbatim README venv/Miniconda/uv bootstrap tests.
- Include completed acceptance evidence and updated installation/validation documentation in the Test Kit. Preserve existing published releases.

## 0.3.0 - 2026-09-29

### Added

- Frequency (legacy), balanced, and cross-position diversity split strategies with shared uncertainty-aware eligibility rules.
- `--tree-mode` and desktop selection of one view or all views from a single alignment.
- Named tree-family folders, mode-aware group assignments, comparison and mutation-use tables, expanded all-mode workbooks, and multi-view HTML/PDF reports.
- Unique original-record reference selection through `--reference-id` and the desktop window.
- Structured tool/version/command provenance and content-based analysis fingerprints.
- Frozen v0.2.3 tree hashes, independent strategy oracles, property-based tests, and a reproducible tree-construction benchmark.
- Complete venv/pip, conda/Miniconda, and uv installation/run examples.

### Changed

- Disable multithreaded MAFFT iterative refinement by default with `--threadit 0`; retain the older flags through `--legacy-alignment`.
- Normalize unsafe, reserved, Unicode-equivalent, and overlong output names, with preflight collision detection.
- Require every requested mode and continuation image before reporting completion.
- Retain root-level filenames as primary-view compatibility outputs; all-mode runs use frequency as the primary view.

### Compatibility

- The frequency split rule, encounter-order ties, thresholds, node numbering, and membership semantics are unchanged for the same mutation observations.
- Different alignment settings can change observations; use matched tool versions and `--legacy-alignment` when comparing historical analyses.
- Alternative tree views are exploratory, not evolutionary reconstructions or confidence measures.


## 0.2.3 — 2026-09-28

- Revised installation and testing instructions for general use and clarified desktop labels.
- Updated package, citation, and installation-guide versions together.
- Added downloadable wheels, source archives, example reports, and a test kit with checksums.
- Added release packaging and publication after the full CI suite passes on main.
- Analysis behavior and output formats are unchanged from 0.2.2.

## 0.2.2 — 2026-09-28

- Added full and simplified plain-text tree traces with node IDs, counts, percentages, hierarchy, and stopping/pruning explanations.
- Added editable Graphviz DOT trees containing decision-tree nodes and edges. Graphviz is optional for users.
- Added one full-tree terminal-group assignment per record, exported as TSV and directly in Excel Records with group size and complete decision path.
- Linked the new outputs from the offline report and included them in the completion gate.
- Made CLI completion explicit: exact output file count, dataset count, absolute results path, key filenames and purposes, and the first file to open.
- Added portable-export tests, native Graphviz rendering in CI, and a short manual acceptance-test guide. Retained exact 100% statement and branch coverage.

## 0.2.1 — 2026-09-28

- Preserve `?`, `U`, and `O` positions as unknown residues before MAFFT. Previously MAFFT could silently remove `?` and shift mutation coordinates. Remove and record a single terminal stop, reject internal stops, pre-gapped inputs, empty IDs, and wholly unknown windows.
- Use compact alignment IDs to prevent MAFFT header truncation, restore full IDs and original order, and stop if any extracted residue is changed or removed.
- Analyze and retain an exact input snapshot so the provenance checksum always describes the data used, even if the source changes during a run.
- Use exact decimal split thresholds: 7/100 now correctly qualifies at a requested minimum frequency of 0.07.
- Explain short reference windows and record pruning reasons consistently in HTML, JSON, and the workbook.
- Require all primary visual/data exports before completion, record interrupted runs as failed, and show workbook creation errors through the CLI.
- Added adversarial regressions, randomized partition checks against an independent observation oracle, and real MAFFT checks for unknown coordinates and long IDs. Retained exact 100% package statement and branch coverage gates.

## 0.2.0 — 2026-09-28

- Added a desktop file-picker with example data, visible progress, and an Open Results button.
- Preserved existing CLI invocation and added `--demo`, `--gui`, `--open`, and `--version`.
- Replaced the PDF's text-only tree with node-and-edge diagrams. Added full/pruned tree PDFs, editable SVGs, and PNGs with continuation pages for larger trees.
- Added an offline expandable HTML report and Excel workbook with sequence metadata, mutations, node paths, and record membership.
- Added input/config validation, protected run directories, failure/completion manifests, retained MAFFT logs, and provenance.
- Scientific corrections: mutation positions now advance only for non-gap reference residues; frequency thresholds use a ceiling; ambiguous/deleted observations are explicit and prevent unsupported negative splits. These can change results relative to 0.1.
- Preserved dataset-mode reference selection and input-order tie handling. Reports explain reference choice, numbering, missing data, pruning, and sequence-count semantics.
- Added 100% package statement/branch coverage gates, real MAFFT and desktop/browser integration checks, artifact checks, and clean-wheel validation.

## 0.1.0

Initial public release of the FluTrees analysis pipeline.
