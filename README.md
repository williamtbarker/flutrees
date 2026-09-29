# FluTrees

[![CI](https://github.com/williamtbarker/flutrees/actions/workflows/ci.yml/badge.svg)](https://github.com/williamtbarker/flutrees/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/williamtbarker/flutrees)](LICENSE)

FluTrees converts influenza HA protein FASTA files into interpretable **mutation decision trees**, PDF reports, an Excel workbook, and portable data files. Analysis runs locally; sequences are not uploaded.

**Version 0.3.0 aligns each dataset once and can build three complementary tree views from the same records, reference, and mutation observations.** The original frequency-based split rule remains the default. These trees organize observed substitutions; they are **not phylogenetic reconstructions**.

```bash
flutrees --demo --tree-mode all --open
```

After installation, this command processes the bundled synthetic example and opens the results overview. For desktop file selection, run `flutrees --gui`.

## What changed in 0.3.0

| Upgrade | Behavior |
|---|---|
| Frequency, balanced, and diversity trees | Choose one view or generate all three without repeating alignment. |
| Legacy compatibility | Frequency remains the default; frozen v0.2.3 fixtures verify exact tree topology, IDs, memberships, and stopping reasons for the same mutation observations. |
| Cross-view comparisons | Compare root splits, group counts, depth, pruning, mutation use, and per-record assignments in HTML, TSV, and Excel. |
| Explicit reference selection | `--reference-id` selects one unique original FASTA ID. The default remains the modal aligned sequence. |
| Reproducibility | MAFFT iterative refinement is single-threaded by default with `--threadit 0`; pairwise stages can still use the requested threads. |
| Provenance | Record tool versions, exact MAFFT command, input/alignment/observation checksums, analytical settings, and a content/settings fingerprint. |
| Portable output folders | Normalize unsafe characters, reserved device names, Unicode, and overlong stems; reject destination collisions before analysis. |
| Completion checks | Validate every named tree view and its continuation images before marking the run complete. |

Earlier protections remain: residue-preserving unknown normalization, rejection of pre-gapped input and internal stops, compact MAFFT transport IDs, original-order restoration, exact decimal frequency thresholds, uncertainty-aware splits, retained input snapshots, and explicit failure records. See [CHANGELOG.md](CHANGELOG.md) for version history.

## Installation: choose one environment

Requires **Python 3.9 or newer and MAFFT 7**. Python 3.11 is used in the examples below. The desktop window additionally needs Tk and a graphical display. Installation downloads dependencies; subsequent analyses and reports work offline.

Choose **one** of the following methods. Do not activate a conda environment and a separate venv for the same installation. Native Linux is covered by CI; macOS instructions are provided, but native Windows/macOS desktop installation is not covered by the test matrix. On Windows, WSL2 with Ubuntu is the recommended CLI route; copy the complete results folder to Windows to view it.

### 1. Python venv and pip

Install MAFFT first with the appropriate system package manager:

```bash
# Ubuntu/Debian, including Ubuntu under WSL2:
sudo apt-get update
sudo apt-get install -y mafft python3-venv python3-tk git

# macOS, with Homebrew already installed (use this instead of apt):
# brew install mafft
```

Then install FluTrees into its own virtual environment:

```bash
git clone https://github.com/williamtbarker/flutrees.git
cd flutrees
git checkout v0.3.0
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
mafft --version
flutrees --version
flutrees --demo --tree-mode all --threads 1 --outdir results --open

# Analyze your own unaligned HA proteins:
flutrees -i my_HA_proteins.fasta --tree-mode all --outdir results
```

The existing `bash install_mafft.sh --dry-run` helper can preview available package-manager options. It does not install a package manager. A Python installation with Tk is required for `flutrees --gui`; the CLI does not require Tk.

### 2. Conda, with Anaconda's Miniconda installer

Miniconda is Anaconda's smaller installer for conda; the full Anaconda Distribution is not required. An existing Anaconda or Miniconda installation can skip the installer block. Review the applicable installer and repository terms for organizational use.

```bash
# If you do not have conda, install conda using Anaconda's Miniconda:
# Linux x86_64 / Ubuntu under WSL2:
curl -fL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o Miniconda3.sh

# Apple Silicon macOS: use this download INSTEAD of the Linux command:
# curl -fL https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh -o Miniconda3.sh

# Verify the SHA-256 against Anaconda's installer listing before running it:
# Linux: sha256sum Miniconda3.sh
# macOS: shasum -a 256 Miniconda3.sh
bash Miniconda3.sh

# With the default installation directory:
source "$HOME/miniconda3/etc/profile.d/conda.sh"
```

Select the installer matching your OS and architecture. Other platforms should use the [official installation guide](https://www.anaconda.com/docs/getting-started/installation); installer checksums are listed in the [Miniconda archive](https://repo.anaconda.com/miniconda/).

```bash
# Create a separate environment with Python, MAFFT, and Tk:
conda create -n flutrees --override-channels -c conda-forge -c bioconda \
  --strict-channel-priority python=3.11 pip mafft tk -y
conda activate flutrees

# Install the versioned FluTrees wheel from this repository's release:
python -m pip install "https://github.com/williamtbarker/flutrees/releases/download/v0.3.0/flutrees-0.3.0-py3-none-any.whl"
mafft --version
flutrees --version
flutrees --demo --tree-mode all --threads 1 --outdir results --open
flutrees -i my_HA_proteins.fasta --tree-mode balanced --outdir results

# At the end of your session:
conda deactivate
```

MAFFT channel availability depends on platform. The venv/uv routes can instead use a separately installed system MAFFT via `--mafft /full/path/to/mafft`.

### 3. uv

Install MAFFT using the system commands in the venv section. uv installs Python packages and can obtain Python, but does **not** install MAFFT.

```bash
# If you do not have uv, install uv:
curl -LsSf https://astral.sh/uv/install.sh -o uv-install.sh
# Inspect uv-install.sh before executing downloaded code.
sh uv-install.sh
source "$HOME/.local/bin/env"

# Create and activate a dedicated environment:
mkdir -p "$HOME/flutrees-work"
cd "$HOME/flutrees-work"
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install "https://github.com/williamtbarker/flutrees/releases/download/v0.3.0/flutrees-0.3.0-py3-none-any.whl"
mafft --version
flutrees --version
flutrees --demo --tree-mode all --threads 1 --outdir results --open
flutrees -i my_HA_proteins.fasta --tree-mode diversity --outdir results
```

See the [official uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/) for other shells and platforms. A managed Python may need additional Tk support for the desktop window; use the CLI when Tk is unavailable.

### Install from the test kit

Download `FluTrees_v0.3.0_Test_Kit.zip` from the [release](https://github.com/williamtbarker/flutrees/releases/tag/v0.3.0), extract it, and open `START_HERE.html`. It contains an installable wheel, example inputs, complete three-view reports, checksums, and acceptance-test instructions. Python and MAFFT are not bundled. Previewing the reports requires neither.

Within an activated venv or conda environment, install the wheel with:

```bash
python -m pip install package/flutrees-0.3.0-py3-none-any.whl
```

With uv, use `uv pip install package/flutrees-0.3.0-py3-none-any.whl` in the activated uv environment.

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

The default frequency workbook retains seven sheets: **Summary, Records, Mutations, Nodes, Node Membership, QC, Parameters**. Alternative/all-mode workbooks additionally contain **Tree Comparison, Tree Groups, Mutation Use, All Nodes, All Membership**. Filter Tree Groups by `mode` and `full_group_id` to inspect each view's terminal groups. Mutation Use is descriptive, not a significance score or consensus tree.

HTML works offline and does not run scripts. Expand a node or its record list; use browser Find to search visible text. Excel offers full-record filtering. PDF, SVG, PNG, and DOT exports label counts as records rather than confidence scores. Graphviz is optional and needed only to render or rearrange DOT files yourself.

## Scientific assumptions and safeguards

The default input window is **84–284 inclusive**, extracted before alignment. Supply unaligned amino-acid sequences with a consistent starting convention. FluTrees does not infer signal peptides, subtypes, mature-HA coordinates, or mixed segments. Protein and nucleotide alphabets overlap, so sequence letters alone cannot reliably identify a mislabeled nucleotide file.

Pre-gapped input is rejected. A single terminal `*` is removed and recorded; internal stops are rejected. `?`, `U`, and `O` become `X` without shifting positions. Windows with no interpretable amino acids are rejected. Short tails are padded and flagged. Duplicate IDs are made unique while retaining original IDs and headers.

MAFFT runs in amino-acid mode with compact transport IDs. Output IDs, residue preservation, and aligned lengths are checked; public IDs and original input order are restored. The reference defaults to the most common aligned sequence, with first input occurrence breaking a tie. `--reference-id` must match exactly one **original** FASTA ID; missing or duplicated requested IDs stop preflight.

Mutation positions count **ungapped selected-reference residues plus the window-start offset**. They are not standardized H1/H3 numbering. Insertions at reference-gap columns are excluded from this substitution-only analysis. A short selected reference is flagged. Unknown, ambiguous, and deleted observations are recorded separately and cannot be treated as confirmed mutation negatives.

Duplicate sequences count as separate records. Reference choice, sample composition, input order in ties, and the selected window can change labels and topology. Compare these settings before comparing separate analyses. No software test fixture establishes clinical or antigenic validity.

## Reproducibility and completion

By default, `--threadit 0` disables multithreading in MAFFT's iterative refinement stage, following [MAFFT's reproducibility guidance](https://mafft.cbrc.jp/alignment/software/multithreading.html). `--legacy-alignment` restores the prior flag set. The frequency **split rule** is unchanged, but changing alignment settings or MAFFT versions can still change upstream observations. No bit-for-bit equivalence across different tools, versions, platforms, or alignments is promised.

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

Diversity scoring and record-rich exports use more memory and time as datasets grow. The tree benchmark separates split construction from MAFFT and report generation; it is not an end-to-end capacity guarantee. Large membership tables remain subject to Excel's sheet limits. Reduce dataset size or tree depth when needed; export failures must not be interpreted as complete analyses.

## Development and validation

```bash
python -m pip install -e '.[dev]'
ruff check .
xvfb-run -a python -m pytest --cov=flutrees --cov-branch \
  --cov-report=term-missing --cov-report=json --cov-fail-under=100
python -m build
python benchmarks/benchmark_tree_modes.py --output benchmark.json
```

CI runs Python 3.9, 3.11, and 3.13 on Linux. It requires exact **100% statement and branch coverage of `src/flutrees`**, unchanged from the prior release. Tests include frozen legacy tree hashes, independent position-level oracles for all modes, Hypothesis-generated observations and uncertainty masks, real MAFFT, reference/error cases, interruption and missing-artifact failures, workbook/PDF contents, paginated figure geometry, native Graphviz rendering, a desktop example under Xvfb, Chromium report checks, and fresh-wheel execution.

Coverage measures executed code, not scientific validity or absence of all defects. MAFFT, Tk, third-party libraries, installation helpers, and release tooling are outside the Python application coverage denominator. See [docs/VALIDATION_0.3.0.md](docs/VALIDATION_0.3.0.md) for scope and benchmark interpretation.

MIT License. See [LICENSE](LICENSE) and [CITATION.cff](CITATION.cff).
