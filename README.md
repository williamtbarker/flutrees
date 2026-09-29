# FluTrees

[![CI](https://github.com/williamtbarker/flutrees/actions/workflows/ci.yml/badge.svg)](https://github.com/williamtbarker/flutrees/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/williamtbarker/flutrees)](LICENSE)

FluTrees converts influenza HA protein FASTA files into interpretable **mutation decision trees**, PDF reports, an Excel workbook, and portable data files. Analysis runs locally; sequences are not uploaded.

**Version 0.3.1 aligns each dataset once and can build three complementary tree views from the same records, reference, and mutation observations.** The original frequency-based split rule remains the default. These trees organize observed substitutions; they are **not phylogenetic reconstructions**.

```bash
flutrees --demo --tree-mode all --open
```

After installation, this command processes the bundled synthetic example and opens the results overview. For desktop file selection, run `flutrees --gui`.

## What changed in the 0.3 release family

| Upgrade | Behavior |
|---|---|
| Frequency, balanced, and diversity trees | Choose one view or generate all three without repeating alignment. |
| Legacy compatibility | Default frequency runs retain the v0.2.3 alignment flags and split rule. Differential CLI tests compare scientific outputs against pinned v0.2.3 source, in addition to frozen tree fixtures. |
| Cross-view comparisons | Compare root splits, group counts, depth, pruning, mutation use, and per-record assignments in HTML, TSV, and Excel. |
| Explicit reference selection | `--reference-id` selects one unique original FASTA ID. The default remains the modal aligned sequence. |
| Alignment profiles | Frequency alone defaults to legacy flags. Alternative/all modes default to `--threadit 0`. Explicit `--reproducible` or `--legacy-alignment` overrides either default. |
| Provenance | Record tool versions, exact MAFFT command, input/alignment/observation checksums, analytical settings, and a content/settings fingerprint. |
| Portable output folders | Normalize unsafe characters, reserved device names, Unicode, and overlong stems; reject destination collisions before analysis. |
| Completion checks | Validate every named tree view and its continuation images before marking the run complete. |
| Large workbooks and JSON reload | Split oversized tables across numbered worksheets; reject overlong cell values instead of truncating them. Read and structurally validate exported trees with `flutrees.tree_io.read_tree`. |
| Release acceptance | Require 5,000 generated property cases, full HA runs through 25,000 records, repeated alignment comparisons, and execution of the actual README installer blocks. |

Earlier protections remain: residue-preserving unknown normalization, rejection of pre-gapped input and internal stops, compact MAFFT transport IDs, original-order restoration, exact decimal frequency thresholds, uncertainty-aware splits, retained input snapshots, and explicit failure records. See [CHANGELOG.md](CHANGELOG.md) for version history.

## Installation: choose one environment

Requires **Python 3.9 or newer and MAFFT 7**. The desktop window additionally needs Tk and a graphical display. Installation downloads dependencies; subsequent analyses and reports work offline. Choose **one** environment. Do not activate conda and a separate venv together.

The Linux command blocks below are executed directly from this README in release CI, including the `curl` bootstraps. CI uses the candidate commit and wheel through the documented `FLUTREES_REF` and `FLUTREES_PACKAGE` overrides; otherwise the commands install the published release. It supplies the bundled test inputs, not private laboratory data. The installer versions are pinned so the tested commands remain repeatable.

### 1. Python venv and pip

Install system prerequisites first. These commands are for **Ubuntu/Debian**, including Ubuntu under WSL2:

```bash
sudo apt-get update
sudo apt-get install -y mafft python3-venv python3-tk git curl
```

On macOS with Homebrew already installed, use `brew install mafft` instead of `apt`. Use a Python installation with Tk for the desktop window. The CLI does not require Tk.

<!-- install-check: venv -->
```bash
# Create a new checkout; do not run this inside an existing flutrees directory.
git clone https://github.com/williamtbarker/flutrees.git
cd flutrees
git checkout "${FLUTREES_REF:-v0.3.1}"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
mafft --version
flutrees --version

# Complete synthetic demonstration, including all three tree views:
flutrees --demo --tree-mode all --threads 1 --outdir results --run-id demo

# Run the included public HA fixture as a second acceptance check:
flutrees -i tests/data/public_HA.fasta --tree-mode all --threads 1 --outdir results --run-id public

# For your own unaligned HA proteins, use a new run ID:
# flutrees -i my_HA_proteins.fasta --tree-mode all --outdir results --run-id laboratory
# Open the absolute START_HERE.html path printed by the CLI, or add --open.
```

`FLUTREES_REF` is optional and selects another existing tag or commit. Without it, the checkout is pinned to v0.3.1. The existing `bash install_mafft.sh --dry-run` helper previews package-manager options; it does not install a package manager itself.

### 2. Conda, with Anaconda's Miniconda installer

Miniconda is Anaconda's smaller conda installer; the full Anaconda Distribution is not required. Existing Anaconda/Miniconda users should skip the download and installation lines and activate their existing conda installation. The bootstrap below is **Linux x86_64 only**. The `-b` option is a noninteractive installation; review and accept the applicable [Anaconda terms](https://www.anaconda.com/legal) before executing it. Installation into an existing `~/miniconda3` directory is deliberately not forced.

<!-- install-check: conda -->
```bash
# If you do not have conda, install conda using Anaconda's Miniconda:
curl -fL https://repo.anaconda.com/miniconda/Miniconda3-py311_26.7.1-1-Linux-x86_64.sh -o Miniconda3.sh
printf '%s  %s\n' 'a6f98e6e19d5b7897ae887cd6af931eb863459f86ffd1a09cc370124cab0993e' 'Miniconda3.sh' | sha256sum -c -
bash Miniconda3.sh -b -p "$HOME/miniconda3"
source "$HOME/miniconda3/etc/profile.d/conda.sh"

# Create a separate environment with Python, MAFFT, and Tk:
conda create -n flutrees --override-channels -c conda-forge -c bioconda \
  --strict-channel-priority python=3.11 pip mafft tk -y
conda activate flutrees

# Install the published wheel, or a local Test Kit wheel supplied through FLUTREES_PACKAGE:
python -m pip install "${FLUTREES_PACKAGE:-https://github.com/williamtbarker/flutrees/releases/download/v0.3.1/flutrees-0.3.1-py3-none-any.whl}"
mafft --version
flutrees --version
flutrees --demo --tree-mode all --threads 1 --outdir results --run-id demo

# flutrees -i my_HA_proteins.fasta --tree-mode balanced --outdir results --run-id laboratory
conda deactivate
```

For **Apple Silicon macOS**, replace the Linux bootstrap with the following, then run the same environment-creation and analysis commands:

```bash
# If you do not have conda on Apple Silicon macOS:
curl -fL https://repo.anaconda.com/miniconda/Miniconda3-py311_26.7.1-1-MacOSX-arm64.sh -o Miniconda3.sh
printf '%s  %s\n' 'da6322bf9a213536df5ce630da2a249b9fb6d433f439b84be07003a790be6be6' 'Miniconda3.sh' | shasum -a 256 -c -
bash Miniconda3.sh -b -p "$HOME/miniconda3"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
```

Other architectures should use the [official installation guide](https://www.anaconda.com/docs/getting-started/installation). Installer hashes are published in the [Miniconda archive](https://repo.anaconda.com/miniconda/). MAFFT package availability varies by platform. Native Windows/macOS desktop operation is not certified by the Linux CI matrix; Windows users can run the CLI under WSL2 and view the complete results folder in Windows.

### 3. uv

Install MAFFT with the system commands in the venv section first. uv manages Python and Python packages; it does **not** install MAFFT.

<!-- install-check: uv -->
```bash
# If you do not have uv, install uv:
curl -LsSf https://astral.sh/uv/0.12.20/install.sh -o uv-install.sh
# Inspect uv-install.sh before executing downloaded code.
sh uv-install.sh
source "$HOME/.local/bin/env"

# Create and activate a dedicated environment:
mkdir -p "$HOME/flutrees-work"
cd "$HOME/flutrees-work"
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install "${FLUTREES_PACKAGE:-https://github.com/williamtbarker/flutrees/releases/download/v0.3.1/flutrees-0.3.1-py3-none-any.whl}"
mafft --version
flutrees --version
flutrees --demo --tree-mode all --threads 1 --outdir results --run-id demo

# flutrees -i my_HA_proteins.fasta --tree-mode diversity --outdir results --run-id laboratory
```

See the [official uv instructions](https://docs.astral.sh/uv/getting-started/installation/) for other shells and platforms. Managed Python may require additional Tk support for the desktop window; the CLI remains available without Tk. `FLUTREES_PACKAGE` optionally selects an existing local wheel or another package URL; it does not change the installer commands.

### Install from the Test Kit

Download `FluTrees_v0.3.1_Test_Kit.zip` from the [release](https://github.com/williamtbarker/flutrees/releases/tag/v0.3.1), extract it, and open `START_HERE.html`. It contains the installable wheel, example inputs, complete three-view reports, checksums, validation evidence, and acceptance instructions. Python and MAFFT are not bundled; previewing the reports requires neither.

Within an activated venv or conda environment:

```bash
python -m pip install package/flutrees-0.3.1-py3-none-any.whl
flutrees --demo --tree-mode all --threads 1 --open
```

With uv, use `uv pip install package/flutrees-0.3.1-py3-none-any.whl` in the activated environment.

## Choose a tree view

| CLI mode | Rule at each node | Purpose |
|---|---|---|
| `frequency` (Mode A, default) | Maximize the positive-record count among eligible substitutions. Ties keep mutation encounter order. | Put prevalent substitutions first; retain the legacy split rule. |
| `balanced` (Mode B) | Maximize the smaller child group, then positive-record count, then encounter order. | Produce more even population partitions. |
| `diversity` (Mode C) | Maximize the reduction in residue entropy at other completely observed positions. Ties use balance, prevalence, then encounter order. | Group records according to substitutions that organize variation elsewhere in the window. |
| `all` | Build all three using one alignment and one set of mutation observations. | Compare views without introducing separate alignment effects. |

```bash
flutrees -i HA.fasta                             # Frequency / legacy split rule
flutrees -i HA.fasta --tree-mode balanced
flutrees -i HA.fasta --tree-mode diversity
flutrees -i HA.fasta --tree-mode all
flutrees -i HA.fasta --tree-mode all --reference-id unique_reference_ID
flutrees -i HA.fasta --reference auto  # Explicit modal selection; also the default
```

All modes use the same eligibility rules: both children meet `--min-split` and the ceiling of `--min-freq` times the node's record count; any uncertain observation at the candidate position withholds that split. `--max-depth` applies to every view. `--prune-cutoff` changes only the simplified presentation, never the full-tree assignments.

### What diversity measures

At a node with `n` records, let `H_j` be the categorical Shannon entropy of the observed residues at position `j`. For candidate mutation `m`, split records into positive and negative groups of sizes `n+` and `n-`. The score is:

```text
sum over other completely observed positions j:
    H_j(parent) - (n+ / n) H_j(positive) - (n- / n) H_j(negative)
```

The entire candidate position is excluded, including its other alleles. Each position has equal weight; different substitutions at one site are not counted as independent binary features. A position with any uncertain record in the node is excluded from scoring for every candidate. Invariant positions contribute zero. Scores are rounded to 12 decimal places for deterministic tie handling. Zero-gain ties fall back to the balanced rule.

This is an exploratory association-based rule, not supervised information gain against an external phenotype. It can emphasize correlated mutations, sequencing patterns, or sampling composition; it does not establish causality, biological function, antigenic effect, evolutionary ancestry, or greater accuracy. Alternative views may legitimately be identical.

## Desktop and cluster workflows

Run `flutrees --gui`, choose FASTA files or the included example, choose the results folder, and check the residue window. The **Tree view** selector offers all four CLI choices. **Reference ID** is optional; leave it empty for the modal reference. Click **Analyze sequences**, then **Open results**.

```bash
# Several independent datasets; each is aligned once:
flutrees -i first.fasta -i second.fasta -o results --tree-mode all --threads 4

# Explicit residue window and aligner location:
flutrees -i HA.fasta --start 84 --end 284 --mafft /path/to/mafft

# Reproduce the older aligner flag set when comparing historical runs:
flutrees -i HA.fasta --tree-mode frequency --legacy-alignment --threads 1
```

Without `--threads`, FluTrees uses `SLURM_CPUS_PER_TASK` when valid, otherwise eight threads. SLURM defaults to `job<SLURM_JOB_ID>` as the run ID; otherwise a timestamp-based ID is generated. Existing run directories are never overwritten. Supply a new `--run-id` for reruns or multiple tasks sharing a job ID. Run IDs must be portable folder names.

On a cluster, omit `--open` and `--gui`. Copy the **entire results folder** to your workstation for viewing. The CLI reports stages, generated modes, actual file count, absolute output path, and the first file to open.

## Results: start with START_HERE.html

```text
results/<run ID>/<safe dataset name>/
    START_HERE.html              Overview, comparisons, expandable trees
    report.pdf                  Summary, QC, mutation chart, each simplified view
    results.xlsx                Records, mutations, nodes, QC, parameters, comparisons
    tree_full.* / tree_pruned.*  Primary-view compatibility files
    group_assignments.tsv       Primary-view terminal groups
    tree_comparison.tsv         Cross-view summary
    tree_groups.tsv             One terminal group per record per mode
    mutation_use.tsv            First split depth and occurrences by mode
    all_nodes.tsv               All modes and both presentations
    all_membership.tsv          Mode + view + node + record membership
    trees/
        frequency/              Present when requested
        balanced/               Present when requested
        diversity/              Present when requested
    input.fasta                 Exact source snapshot
    extracted.fasta
    mafft_input.fasta            Compact transport IDs
    aligned.fasta               Restored public record IDs
    metadata.tsv
    mutations_per_record.tsv
    mutation_counts.tsv
    summary.json
    provenance.json
    output_manifest.json
    mafft.log
    status.json
```

Each `trees/<mode>/` folder includes full/pruned PDF, PNG, editable SVG, Graphviz DOT, JSON, and plain-text trees, plus group assignments, node tables, and `method.json`. Large trees continue across numbered PDF pages and `_page_002` image files. The unnumbered PNG/SVG is only the first page; no branches are discarded to fit it.

Root-level tree files retain the historical paths. They mirror **frequency** in `all` mode, or the explicitly selected single mode otherwise. `summary.json` records which mode is primary. Every full-tree record belongs to exactly one terminal group per mode. Node and group IDs are local to a mode and a run: join on mode as well as ID when comparing views.

For tables within one worksheet, the default frequency workbook retains seven sheets: **Summary, Records, Mutations, Nodes, Node Membership, QC, Parameters**. Alternative/all-mode workbooks additionally contain **Tree Comparison, Tree Groups, Mutation Use, All Nodes, All Membership**. Filter Tree Groups by `mode` and `full_group_id` to inspect each view's terminal groups. Mutation Use is descriptive, not a significance score or consensus tree. Tables longer than 1,048,575 data rows continue in numbered worksheets, such as **All Membership (2)**, with repeated headers and filters. Read every continuation sheet for the complete table. Excel cells longer than 32,767 characters cause an explicit error rather than silently losing text.

HTML works offline and does not run scripts. Expand a node or its record list; use browser Find to search visible text. Excel offers full-record filtering. PDF, SVG, PNG, and DOT exports label counts as records rather than confidence scores. Graphviz is optional and needed only to render or rearrange DOT files yourself.

## Scientific assumptions and safeguards

The default input window is **84–284 inclusive**, extracted before alignment. Supply unaligned amino-acid sequences with a consistent starting convention. FluTrees does not infer signal peptides, subtypes, mature-HA coordinates, or mixed segments. Protein and nucleotide alphabets overlap, so sequence letters alone cannot reliably identify a mislabeled nucleotide file.

Pre-gapped input is rejected. A single terminal `*` is removed and recorded; internal stops are rejected. `?`, `U`, and `O` become `X` without shifting positions. Windows with no interpretable amino acids are rejected. Short tails are padded and flagged. Duplicate IDs are made unique while retaining original IDs and headers.

MAFFT runs in amino-acid mode with compact transport IDs. Output IDs, residue preservation, and aligned lengths are checked; public IDs and original input order are restored. The reference defaults to the most common aligned sequence, with first input occurrence breaking a tie. `--reference auto` explicitly selects the modal rule and cannot be combined with `--reference-id`. `--reference-id` must match exactly one **original** FASTA ID; missing or duplicated requested IDs stop preflight.

Mutation positions count **ungapped selected-reference residues plus the window-start offset**. They are not standardized H1/H3 numbering. Insertions at reference-gap columns are excluded from this substitution-only analysis. A short selected reference is flagged. Unknown, ambiguous, and deleted observations are recorded separately and cannot be treated as confirmed mutation negatives.

Duplicate sequences count as separate records. Reference choice, sample composition, input order in ties, and the selected window can change labels and topology. Compare these settings before comparing separate analyses. No software test fixture establishes clinical or antigenic validity.

## Reproducibility and completion

A default **frequency-only** run retains the v0.2.3 MAFFT flag set as well as its split rule. This preserves the existing invocation rather than changing upstream alignment silently. The **balanced, diversity, and all** modes default to `--threadit 0`, following [MAFFT's reproducibility guidance](https://mafft.cbrc.jp/alignment/software/multithreading.html). This disables multithreaded iterative refinement while allowing parallel pairwise stages. `--reproducible` enables that profile for any mode; `--legacy-alignment` selects the older flag set for any mode. The effective choice and exact command are recorded.

An `all` run always uses one alignment for every tree. When comparing separate frequency and alternative runs, select the same explicit alignment profile. v0.3.0 used reproducible alignment for all default runs; v0.3.1 restores the historical default for frequency alone. Twelve differential CLI cases compare default and explicit profiles against the pinned v0.2.3 code, checking exact scientific tables, alignments, memberships, and trees on known inputs. This is a regression contract under the same tested dependencies, not a promise of byte identity across different MAFFT versions, platforms, timestamps, or PDF renderers.

`provenance.json` records Python and dependency versions, MAFFT version/path/command, effective settings, reference ID, input and alignment SHA-256 values, and a canonical mutation-observation hash. `analysis_id` fingerprints these contents and settings; timestamps and output locations do not affect it. It is a provenance identifier, not a validation certificate. A failed version probe is disclosed rather than guessed. `mafft.log` retains aligner diagnostics and strategy details.

Only `status.json` with `status: complete` indicates success. Required artifacts, including every continuation image, are checked for existence and nonzero size. Exceptions and Ctrl+C record failure; disk exhaustion or forced process termination can prevent the status update. Partial files are retained for diagnosis. A browser-opening failure does not invalidate completed output.

For practical acceptance checks, see [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md).

## Troubleshooting

| Symptom | Action |
|---|---|
| MAFFT missing | Check `mafft --version`; install it or use `--mafft` with its executable path. |
| No interpretable residues | Check protein translation, sequence length, and `--start`/`--end`. |
| Pre-gapped input or internal stop | Return to the unaligned protein sequence and inspect the translation. |
| MAFFT changed residues or IDs | Inspect input snapshots and `mafft.log`; the run stopped to protect analytical integrity. |
| Reference ID missing or ambiguous | Use a unique original FASTA identifier, not a guessed renamed duplicate. |
| Input filenames collide | Rename them; comparison includes normalized names and case-insensitive collisions. |
| Existing run directory | Choose another run ID; old results are protected. |
| Root-only or sparse tree | Check full versus simplified views, thresholds, reference choice, and uncertainty/QC notes. |
| Tk/display unavailable | Use the CLI and open the results on a desktop machine. |
| Partial exports | Inspect dataset and run `status.json`, then correct the cause and use a new run ID. |

Diversity scoring and record-rich exports use more memory and time as datasets grow. Release acceptance runs the full HA-input/alignment/all-view/export pipeline at 100, 500, 1,000, 5,000, 10,000, and 25,000 records and checks record conservation in JSON, TSV, and the workbook. That fixture repeats unmodified public HA proteins with distinct IDs; it is not 25,000 independent biological observations or a guarantee for every degree of sequence diversity. Stage timings and resource measurements are included in the Test Kit. Excel row limits are handled with continuation sheets, but memory, disk capacity, and extreme cell lengths still matter. Export failures must not be interpreted as complete analyses.

## Development and validation

```bash
python -m pip install -e '.[dev]'
# The differential tests verify this exact historical source:
git worktree add --detach validation/legacy 5683105e015e19ccaa5744789de9ad8941331975
ruff check .
xvfb-run -a python -m pytest --cov=flutrees --cov-branch \
  --cov-report=term-missing --cov-report=json --cov-fail-under=100
python -m build
python benchmarks/benchmark_tree_modes.py --output benchmark.json
python benchmarks/benchmark_end_to_end.py --outdir validation/ha-performance
python benchmarks/benchmark_alignment.py --outdir validation/alignment-comparison
```

CI runs Python 3.9, 3.11, and 3.13 on Linux. It requires exact **100% statement and branch coverage of `src/flutrees`**, unchanged from the prior release. Tests include 30 frozen legacy tree hashes, 12 differential legacy/current CLI runs, independent position-level oracles for all modes, 5,000 Hypothesis-generated datasets and uncertainty masks, JSON reload/round trips, a real Excel worksheet-boundary test, real MAFFT, reference/error cases, interruption and missing-artifact failures, workbook/PDF contents, paginated figure geometry, native Graphviz rendering, a desktop example under Xvfb, Chromium report checks, and fresh-wheel execution.

Coverage measures executed code, not scientific validity or absence of all defects. MAFFT, Tk, third-party libraries, installation helpers, and release tooling are outside the Python application coverage denominator. See [the acceptance matrix](docs/ACCEPTANCE.md) and [v0.3.1 validation scope](docs/VALIDATION_0.3.1.md). Release packages include the completed run's actual installer transcripts, benchmark measurements, test report, and coverage data. The [v0.3.0 validation record](docs/VALIDATION_0.3.0.md) is retained as historical documentation.

MIT License. See [LICENSE](LICENSE) and [CITATION.cff](CITATION.cff).
