# FluTrees 0.2.3

FluTrees converts influenza HA protein FASTA files into mutation decision trees, reports, and tables for sequence review.

## Download and start

Download `FluTrees_v0.2.3_Test_Kit.zip`, extract it, and open `START_HERE.html`. It includes an installable Python wheel, example inputs, complete example outputs, and installation instructions. Python 3.9 or newer and MAFFT are required to run an analysis; neither is bundled. The example reports can be viewed without installing FluTrees.

The wheel and source archive are also available separately. `SHA256SUMS.txt` lists the release asset checksums.

## Included features

- Desktop file selection and progress display, plus the existing command-line workflow.
- A PDF report and full/simplified tree PDFs, with continuation pages for larger trees.
- Plain-text tree traces, PNG images, editable SVG figures, and Graphviz DOT files.
- An offline expandable HTML report and a seven-sheet Excel workbook with record-level group assignments.
- JSON, TSV, and FASTA exports, input snapshots, parameters, and completion/failure records.
- CLI completion messages stating the file count, absolute results path, output filenames, and the first file to open.

## Changes in 0.2.3

Updated installation and testing instructions, desktop labels, version metadata, and release packaging. Analysis behavior is unchanged from 0.2.2. See `CHANGELOG.md` for the scientific corrections introduced in 0.2.0 and 0.2.1, which can change mutation labels or groups compared with 0.1.0.

## Verification and interpretation

Release publication requires the test suite, exact 100% statement and branch coverage of `src/flutrees`, real MAFFT and desktop checks, Chromium report checks, native Graphviz rendering, and clean-wheel example runs. CI runs on Linux with Python 3.9, 3.11, and 3.13. Native Windows/macOS installation is not covered by that matrix.

These are mutation decision trees, not phylogenies. Verify the input residue window, selected reference, numbering convention, and quality notes before interpreting laboratory data. The bundled synthetic and public HA datasets are software test fixtures.
