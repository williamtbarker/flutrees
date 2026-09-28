# Changelog

## 0.2.1 — 2026-09-28

- Adversarial scientific fix: preserve `?`, `U`, and `O` positions as unknown residues before MAFFT. Previously MAFFT could silently remove `?` and shift mutation coordinates. Remove and record a single terminal stop, reject internal stops, pre-gapped inputs, empty IDs, and wholly unknown windows.
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
