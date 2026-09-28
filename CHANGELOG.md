# Changelog

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
