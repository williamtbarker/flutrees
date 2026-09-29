# FluTrees

[![CI](https://github.com/williamtbarker/flutrees/actions/workflows/ci.yml/badge.svg)](https://github.com/williamtbarker/flutrees/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/williamtbarker/flutrees)](LICENSE)

FluTrees organizes influenza HA protein sequences into interpretable mutation decision trees. It supports sequence review in seasonal vaccine surveillance and development workflows.

**Choose protein FASTA files, run the analysis, and open `START_HERE.html`.** Each run produces visual trees, a PDF report, an Excel workbook, and the underlying sequence and analysis files. Your data stays on your computer.

## Desktop workflow

After the one-time installation below, launch the desktop window:

```bash
flutrees --gui
```

1. Click **Use included example** to try the complete workflow, or **Choose FASTA files** for your own protein sequences.
2. Choose a results folder and check the residue window. The default is **84–284 inclusive**, a 201-amino-acid window.
3. Click **Analyze sequences**. The window shows progress while MAFFT aligns the sequences and FluTrees prepares the reports.
4. Click **Open results**. Select the dataset and open its PDF, workbook, or expandable tree.

The alternative command `flutrees-gui` opens the same window. The launcher needs Python with Tk support and a desktop display. On a cluster, use the command-line workflow and copy the **whole results folder** to your computer to view it.

### Try the example without the desktop window

```bash
flutrees --demo --open
```

This runs 48 deliberately synthetic protein records through real MAFFT. It is a software demonstration, not an influenza reference panel or scientific validation dataset. `--open` opens the results overview in your browser; omit it on a cluster.

## Which result should I open?

| What you want | Open this |
|---|---|
| See what ran and where to go next | `START_HERE.html` |
| Read the summary, quality notes, mutation chart, and visual tree | `report.pdf` |
| Filter records, mutations, and group memberships in Excel | `results.xlsx` |
| See every branch across readable pages | `tree_full.pdf` |
| See a simplified tree with small groups hidden | `tree_pruned.pdf` |
| Paste a figure into a slide | `tree_pruned.png` or `tree_full.png` |
| Edit a figure in a vector graphics application | `tree_pruned.svg` or `tree_full.svg` |
| Read or copy the entire tree as plain text | `tree_full.txt` or `tree_pruned.txt` |
| Rearrange the tree in Graphviz | `tree_full.dot` or `tree_pruned.dot` |
| Trace each record to its final group | `group_assignments.tsv`, or the group columns in Excel Records |
| Reuse the analysis in another tool | JSON, TSV, and FASTA files |

Large trees continue across numbered PDF pages. The unnumbered PNG and SVG show the first page; additional images use `_page_002`, `_page_003`, and so on. No branches are silently cut off to fit the page.

The HTML report works offline. Click a group to collapse or expand it, or **Show records in this group** to see its members. Browser zoom works normally. Use the browser's Find command to search visible text; expand the record list to search it. Full-text filtering across all records is available in the workbook.

The workbook contains **Summary**, **Records**, **Mutations**, **Nodes**, **Node Membership**, **QC**, and **Parameters**. In Records, filter **full_group_id** to select a final group immediately; **full_group_size** gives its record count and **full_group_path** traces every decision leading to it. Every record receives exactly one full-tree terminal group, including groups hidden in the simplified view. Group IDs are local to a run and may change between analyses.

For intermediate nodes, filter Node Membership by `view` (`full` or `pruned`) and `node_id`; connect to Records using `record_id`. Parent IDs and complete paths are included in Nodes. The plain-text trees retain every node, indentation, record count, percentage, and stopping/pruning explanation. DOT files preserve the editable graph topology without adding evolutionary branch lengths; Graphviz is optional and is not needed to generate any output.

For a first run on your own computer, follow the [short acceptance-test guide](docs/TESTING_GUIDE.md).

## One-time installation

Download the **Test Kit ZIP** from the [latest release](https://github.com/williamtbarker/flutrees/releases/latest) for an installable wheel, example inputs, complete example reports, and an installation guide. Unzip it and open `START_HERE.html` to preview the reports before installing. Python and MAFFT are required to run a new analysis.

Requires Python 3.9 or newer and [MAFFT](https://mafft.cbrc.jp/alignment/software/). Install in a virtual environment:

```bash
git clone https://github.com/williamtbarker/flutrees.git
cd flutrees
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
mafft --version
flutrees --demo --open
```

On Windows, activate the environment with `.venv\Scripts\activate` in Command Prompt. MAFFT must be installed for the operating system and available on PATH. The desktop launcher also requires Tk; use a Python installation that includes it. On Ubuntu, the Tk package is `python3-tk`.

Common MAFFT installation commands:

```bash
# macOS with Homebrew
brew install mafft

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install mafft python3-tk
```

The existing `bash install_mafft.sh` helper can also try available package managers. `bash install_mafft.sh --dry-run` previews its actions. It does not install a package manager itself.

For an existing installation, update from this repository and reinstall:

```bash
git pull --ff-only
python -m pip install .
flutrees --version
```

## Command-line and cluster workflow

Existing invocations remain valid:

```bash
flutrees -i my_HA_proteins.fasta -o results
flutrees -i first.fasta -i second.fasta -o results --threads 4
flutrees -i my_HA_proteins.fasta --start 84 --end 284 --mafft /path/to/mafft
```

Use `flutrees --help` to see all parameters. Input files must have distinct filename stems; duplicate destinations are rejected before analysis. Existing run directories are never overwritten. Use a new `--run-id` for a rerun, or let FluTrees generate one.

Results are in `results/<run ID>/<input filename>/`. On SLURM, the default run ID is `job<SLURM_JOB_ID>`, and the thread count uses `SLURM_CPUS_PER_TASK` when available. Reusing the same job/run ID requires a different `--run-id`.

The CLI shows each processing stage and finishes with the exact number of files created, dataset count, absolute results-folder path, key output filenames and their purposes, and the `START_HERE.html` file to open first.

## Interpreting the science

- **This is a mutation decision tree, not a phylogenetic reconstruction.** A branch partitions records by presence of a called amino-acid substitution. Counts are sequence records, including duplicate sequences, not confidence or bootstrap support.
- Each input file is analyzed separately. FluTrees extracts the requested input-residue window before alignment. Supply amino-acid sequences with a consistent starting/numbering convention; it does not detect signal peptides, subtype numbering schemes, or mixed HA segments automatically.
- Supply **unaligned** protein FASTA, without `-` gap characters. A gapped alignment counts columns differently from residues and is rejected before analysis. A single terminal `*` is removed and recorded; internal stop markers require checking the translation. `?`, `U`, and `O` are represented as `X` (unknown) and flagged, preserving their positions. Windows consisting entirely of unknown residues are rejected.
- MAFFT runs in amino-acid mode. The reference is the most common aligned sequence within that input file. A tie selects the first occurrence. The actual reference ID and sequence are recorded in `summary.json`.
- FluTrees uses compact IDs when calling MAFFT, then restores full original IDs and input order. It verifies that alignment preserved every extracted residue. The `alignment_id` column links the diagnostic `mafft_input.fasta` file to Records. A short selected reference is explicitly flagged because positions outside it cannot be compared.
- Each dataset retains an exact `input.fasta` snapshot. Its checksum identifies the bytes actually analyzed, even if the source file is edited while a run is in progress.
- Mutation labels use **ungapped selected-reference residue positions, offset by the selected window start**. They are not a mapping to standardized H3, H1, or mature-HA numbering. Insertions relative to the chosen reference are outside this substitution-only analysis.
- Missing, ambiguous, and deleted residues are recorded as `uncertain_positions`. A candidate split is withheld if any record in the node has an uncertain observation at that position, so missing evidence is not labeled as a confirmed negative.
- Among eligible splits, the most frequent substitution is selected; ties preserve input/mutation encounter order. Both children must meet the minimum record count and frequency. The fractional threshold is enforced with a ceiling.
- Short sequences are padded and flagged. Empty selected windows, invalid sequence characters, malformed alignments, and invalid parameter ranges stop the run with an explanation.
- Pruning affects presentation, not the full tree. Hidden groups are explained in the report. A tree with no visible subdivisions can result from identical sequences, small sample size, missing observations, thresholds, or pruning.

Version 0.2 corrects residue numbering after reference gaps, fractional-threshold rounding, and missing-observation handling. These corrections can change mutation labels or groups compared with 0.1; review them when comparing historical analyses. The original numbering convention and first-window extraction should be checked against your laboratory's inputs before scientific interpretation.

Version 0.2.1 additionally prevents residue loss during alignment and uses exact decimal frequency thresholds (for example, 7 of 100 records qualifies at 0.07). See the [adversarial review](docs/adversarial-review-2026-09-28.md) for reproduced defects, fixes, and remaining validation limits.

## When something goes wrong

| Message or symptom | What to do |
|---|---|
| MAFFT was not found | Install MAFFT and check `mafft --version`; the CLI also accepts `--mafft /full/path/to/mafft`. |
| No residues in the selected window | Check the sequence lengths and the First/Last residue settings. |
| Input contains alignment gaps | Supply the original unaligned proteins. Do not assume existing alignment columns are residue coordinates. |
| Internal stop marker | Check the translation and sequence quality; only a single terminal stop is removed automatically. |
| MAFFT changed or removed residues | Inspect the original input and `mafft_input.fasta`; the analysis has stopped to protect residue numbering. |
| Input filenames share an output folder | Rename the input files so their names differ, even if they live in different folders. |
| A run directory already exists | Choose a new run ID; previous results are protected. |
| MAFFT failed | Open `mafft.log` in that dataset's folder. |
| No desktop display | Run the CLI on the cluster, then open the entire results folder on your own computer. |
| JSON exists but the report is missing | Read `status.json`; the run may have failed during export. A complete run lists its artifacts. |
| The simplified tree shows only one group | Open the full tree and read the QC notes; small groups may be hidden by the pruning cutoff. |

The program only reports completion once all required exports, including the overview PNG/SVG figures and data tables, are present and nonempty. Partial artifacts and a failure status are retained for diagnosis. Interrupting a command-line run with Ctrl+C marks it as failed; a forcibly terminated process may leave a running status, which is not a completed analysis. A browser failing to open does not delete or invalidate the completed results.

## Development and testing

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest --cov=flutrees --cov-branch --cov-report=term-missing --cov-fail-under=100
python -m build
```

CI enforces **100% statement and branch coverage of every module in `src/flutrees`**, including the CLI, desktop launcher, reporting, and error handling. Third-party MAFFT, Python/Tk, spreadsheet libraries, and the existing operating-system installation helper are outside the Python package coverage denominator.

Coverage is supplemented with real MAFFT runs, a desktop example under Xvfb, a Chromium check of the offline report, workbook and PDF content assertions, graphical layout checks, input/error regressions, and a clean wheel installation. CI exercises Python 3.9, 3.11, and 3.13 on Linux. Native Windows/macOS desktop installation is not covered by this CI matrix.

Tests marked `integration` require MAFFT; `gui` requires a display. CI provides both and executes them. Chromium is installed for the separate browser job. The included synthetic example is bundled in both wheel and source distributions.

MIT License. See [LICENSE](LICENSE).
