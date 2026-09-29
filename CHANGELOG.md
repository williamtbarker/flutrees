# Changelog

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
