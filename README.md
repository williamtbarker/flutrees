# FluTrees

[![CI](https://github.com/williamtbarker/flutrees/actions/workflows/ci.yml/badge.svg)](https://github.com/williamtbarker/flutrees/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/williamtbarker/flutrees)](LICENSE)

FluTrees converts influenza HA protein FASTA files into interpretable **mutation decision trees**, PDF reports, an Excel workbook, and portable data files. Analysis runs locally; sequences are not uploaded.

**Version 0.3.2 adds a complete desktop workspace with editable analysis settings, file management, progress logs, copyable CLI commands, and a fitted tree viewer with adjustable layout.** Each dataset is aligned once and can produce three complementary tree views from the same records, reference, and mutation observations. The original frequency-based split rule remains the default. These trees organize observed substitutions; they are **not phylogenetic reconstructions**.

**Start here:** [Quickstart: GUI Mode](#quickstart-gui-mode) · [Installation](#installation-choose-one-environment) · [CLI and cluster workflows](#desktop-and-cluster-workflows) · [Troubleshooting](#troubleshooting)

## Quickstart: GUI Mode

Use the desktop window to select sequences, run an analysis, and adjust your tree figures. You do not need to write code. If FluTrees already opens on your computer, skip installation and start with the example below. Otherwise, complete [one installation method](#installation-choose-one-environment) first; the GUI needs Python with Tk support and the MAFFT aligner. Graphviz and developer testing tools are not required for this walkthrough.

### 1. Open FluTrees

Open Terminal, activate the environment where you installed FluTrees, and enter:

```bash
flutrees --gui
```

`flutrees-gui` opens the same window. With conda, activate your installation with `conda activate flutrees`. With the venv installation below, open the `flutrees` checkout folder in Terminal and run `source .venv/bin/activate` first. Use the environment you installed into, rather than creating a new one each time. Keep Terminal open while using the window.

### 2. Try the included example

Start with a newly opened window so the settings are at their defaults.

1. On **Analysis**, click **Use included example**. The file list should show the bundled example, containing 48 synthetic protein records.
2. Leave **Results folder** at its default, `FluTrees_results` in your home folder. Leave **Run ID** blank to create a new timestamped folder automatically.
3. Leave the analysis settings unchanged: residues **84–284**, **frequency**, **Max depth 10**, **Min split 5**, **Min freq 0.05**, and **Prune cutoff 10**. Leave **Reference ID** blank.
4. Click **Analyze sequences**. Check **Run log** for progress. The moving bar means the program is working; it is not a percentage complete. Controls unlock when the run finishes.
5. When the status says **Complete**, click **Open results**. Your browser opens a local results page; click the example dataset to see its report, tree figures, and workbook.

The example demonstrates four groups of 12 records. It is a software demonstration, not a biological reference panel. If you use **Use included example** later, it replaces the selected files and resets the residue window, but retains your other settings.

### 3. Run your own sequences

On **Analysis**, click **Clear** to remove the example, then **Add FASTA files...** to choose your data. Supply **unaligned HA protein sequences (amino acids)**, not nucleotide sequences or an already aligned FASTA. Put sequences you want compared together in one file: multiple selected files are analyzed as separate datasets.

Choose a **Results folder** you can find again. Give the run a descriptive **Run ID**, such as `HA_batch1`, or leave it blank. Use a new name for each run; FluTrees never overwrites an existing run folder.

Check **First residue** and **Last residue** before starting. The default is **84–284, inclusive**, counted from the first amino acid in each input sequence. FluTrees extracts this window before alignment; it does not automatically convert between full-length HA, mature HA, or H1/H3 numbering. Inputs should use the same starting convention.

Leave **Reference ID** blank to use the most common aligned sequence. To select a reference yourself, enter its exact FASTA identifier: the text immediately after `>` up to the first space. That identifier must occur exactly once in each selected file.

For your first analysis, keep the other defaults and click **Analyze sequences**. To adjust the grouping later:

| GUI setting | What it controls | How to use it |
|---|---|---|
| **Tree view** | Which rule chooses each split. | Start with **frequency**. Choose **all** to compare frequency, balanced, and diversity trees from one alignment. See [Choose a tree view](#choose-a-tree-view) before interpreting their differences. |
| **Max depth** | How many successive splits a path can contain. | Default **10**. Lower it for a shallower tree; **0** shows only the starting group. Raising it allows, but does not guarantee, more splits. |
| **Min split** | Minimum number of records required in **each** child group. | Default **5**. Raise it to prevent splits that create very small groups. |
| **Min freq** | Minimum fraction of the current parent group required in **each** child. | Default **0.05**, meaning **5%**. Enter a fraction, not `5`. Both this setting and Min split must be satisfied. |
| **Prune cutoff** | Hides smaller groups in the simplified (`pruned`) view. | Default **10**. Changes the simplified display; the full tree and its record assignments are retained. |

For example, with 200 records in a parent group, Min freq **0.05** requires at least 10 records in each child, even when Min split is **5**. These thresholds affect which groups can appear; a larger or more detailed tree is not automatically more biologically informative.

The **Advanced** tab can stay at its defaults for this walkthrough. If you compare separate analyses, keep the reference, residue window, alignment profile, and thread count consistent. Full details and valid ranges are in the [parameter reference](docs/GUI_CLI_PARAMETERS.md).

### 4. Read the results

Click **Open results**, then select your dataset. Start with:

| File | Use it for |
|---|---|
| **START_HERE.html** | Browse the analysis overview, quality notes, trees, and links to other outputs. |
| **report.pdf** | Read the summary and simplified tree figures in a printable report. |
| **results.xlsx** | Inspect records, mutations, group membership, quality checks, and the settings used. |
| **tree_full.pdf** | Follow the complete tree, including continuation pages for larger trees. |

Read a tree from left to right. A label such as **A123T** identifies a substitution relative to the selected reference; **Not A123T** is the other side of that split. Counts are sequence records, and percentages use all input records. They are not confidence scores. These are **mutation decision trees, not evolutionary trees**.

### 5. Adjust the figure and save it

Open **Tree viewer** and use the dropdown to choose a dataset, tree view, and `tree_full.json` or `tree_pruned.json`. The full tree retains all groups; the pruned tree is the simplified presentation.

| Control | What to do |
|---|---|
| **Width / Height** | Set the page size in inches. Try width **12**, height **8** for landscape, or width **8**, height **12** for portrait. |
| **Level gap** | Increase the horizontal gap between successive splits; try **1.5**. |
| **Node gap** | Increase the vertical gap between node boxes; try **1.5**. |
| **Line width** | Adjust branch thickness; the default is **1.5** points. |
| **Apply layout** | Apply your changed values to the displayed page. |
| **Whole page** | Show the page shape, title, and margins. Turn it off to focus on the tree itself. |
| **Fit / Zoom + / Zoom -** | Fit the current page's tree to the window or inspect it more closely. Drag to pan when zoomed in. |
| **Previous page / Next page** | Follow continuation pages when the tree is too large for one page. |
| **Save page...** | Save the displayed page as PDF, SVG, or PNG. Choose a new filename or folder for your adjusted figure. |

The viewer fits each page automatically. Increasing spacing within a fixed page can make labels smaller, so adjust width and height too when needed. Use **Whole page** to judge the exported proportions; zoom changes your screen view, not the exported page size.

**Apply layout** and **Save page...** do not rerun alignment or change your scientific results. Saving exports **one page**, not the whole tree or report, and uses the last applied layout. To generate all tree pages and the report with a new layout, set the layout fields first, then run the analysis again with a new Run ID.

### 6. Come back to a run or share it

Your results remain on disk after you close FluTrees. To reopen the overview, open `START_HERE.html` inside your run folder. To adjust an old tree, choose **Tree viewer → Open saved run...** and select the **run folder** inside `FluTrees_results`, not the outer results folder or an individual dataset folder. The viewer uses the current layout fields when opening a saved run.

To share results, copy or zip the **entire run folder** so its links and supporting files stay together. Recipients can open its HTML reports without installing FluTrees. Before sharing, check that the included sequence data and identifiers are appropriate for the recipient.

**If something goes wrong:** a used Run ID needs a new name; a missing MAFFT error needs the aligner installed or its path entered under **Advanced → MAFFT executable**. For a root-only tree, inspect the full tree and quality notes before lowering thresholds. If controls are disabled, check **Run log** and wait for the active run to finish. See [Troubleshooting](#troubleshooting) for other cases.

## What changed in the 0.3 release family

| Upgrade | Behavior |
|---|---|
| Desktop parameter access | Edit every existing analysis setting, including depth, split count, frequency, pruning, alignment, and a custom run name. |
| Adjustable tree layout | Set aspect ratio, horizontal/vertical gaps, and branch weight; inspect fitted pages, zoom/pan, and save a restyled page without rerunning MAFFT. |
| Desktop workflow | Add/remove files, use grouped Analysis/Advanced tabs, inspect the run log, and copy an equivalent CLI command. |
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

On macOS with Homebrew already installed, check `mafft --version` first; if MAFFT is missing, use `brew install mafft` instead of `apt`. Use a Python installation with Tk for the desktop window; `python3 -m tkinter` opens a small test window when Tk is available. Close it before continuing. Retain working prerequisites instead of reinstalling them. The CLI does not require Tk.

<!-- install-check: venv -->
```bash
# Create a new checkout; do not run this inside an existing flutrees directory.
git clone https://github.com/williamtbarker/flutrees.git
cd flutrees
git checkout "${FLUTREES_REF:-v0.3.2}"
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

`FLUTREES_REF` is optional and selects another existing tag or commit. Without it, the checkout is pinned to v0.3.2. The existing `bash install_mafft.sh --dry-run` helper previews package-manager options; it does not install a package manager itself.

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
python -m pip install "${FLUTREES_PACKAGE:-https://github.com/williamtbarker/flutrees/releases/download/v0.3.2/flutrees-0.3.2-py3-none-any.whl}"
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
uv pip install "${FLUTREES_PACKAGE:-https://github.com/williamtbarker/flutrees/releases/download/v0.3.2/flutrees-0.3.2-py3-none-any.whl}"
mafft --version
flutrees --version
flutrees --demo --tree-mode all --threads 1 --outdir results --run-id demo

# flutrees -i my_HA_proteins.fasta --tree-mode diversity --outdir results --run-id laboratory
```

See the [official uv instructions](https://docs.astral.sh/uv/getting-started/installation/) for other shells and platforms. Managed Python may require additional Tk support for the desktop window; the CLI remains available without Tk. `FLUTREES_PACKAGE` optionally selects an existing local wheel or another package URL; it does not change the installer commands.

### Install from the Test Kit

Download `FluTrees_v0.3.2_Test_Kit.zip` from the [release](https://github.com/williamtbarker/flutrees/releases/tag/v0.3.2), extract it, and open `START_HERE.html`. It contains the installable wheel, example inputs, complete three-view reports, checksums, validation evidence, and acceptance instructions. Python and MAFFT are not bundled; previewing the reports requires neither.

Within an activated venv or conda environment:

```bash
python -m pip install package/flutrees-0.3.2-py3-none-any.whl
flutrees --demo --tree-mode all --threads 1 --open
```

With uv, use `uv pip install package/flutrees-0.3.2-py3-none-any.whl` in the activated environment.

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

Run `flutrees --gui` or `flutrees-gui`. The native desktop workspace uses the same analysis engine and configuration as the CLI.

- **Analysis:** add multiple FASTA files, inspect their locations, remove selected files, or try the included example. Choose the results folder and optional Run ID; set the residue window, tree view, reference, Max depth, Min split, Min freq, and Prune cutoff.
- **Advanced:** set the MAFFT executable, CPU threads, and alignment profile. Blank threads retain the SLURM/eight-thread default. Mode default retains legacy alignment for frequency-only runs and reproducible alignment for alternative/all views.
- **Tree viewer:** set page width/height, level gap, node gap, and line width. Inspect full or pruned trees after a run, or open a saved completed run. Apply layout, preview the whole page or fit the tree itself, move between continuation pages, zoom, drag to pan, and save the displayed page as PNG/SVG/PDF.
- **Run log:** see each session run's command, progress messages, results location, and errors. The action buttons and status remain visible while switching tabs. Analysis settings scroll in smaller windows.

Click **Analyze sequences**, then **Open results**. Settings lock while a run is active and unlock afterward. Invalid values or an existing run name are rejected before starting. Pipeline preflight continues to check inputs, references, and MAFFT before creating a run folder. The progress bar indicates activity, not a percentage or estimated finish time.

**Copy CLI command** copies the current settings without running an analysis. Commands are quoted for POSIX shells on macOS/Linux or PowerShell on Windows. Blank Run ID generates a new timestamp for each copy or analysis; specify a name if you need an exact folder name. The run log records the command actually submitted. Change the run name before repeating a completed command. The GUI's automatic names remain timestamp-based; the CLI retains its SLURM job-name convention.

See the [complete GUI/CLI parameter map](docs/GUI_CLI_PARAMETERS.md) for defaults, ranges, and scientific interpretation. `--gui` opens the desktop with its own defaults; it does not prefill fields from additional CLI analysis flags.

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

For a portrait tree export with more space between nodes:

```bash
flutrees -i HA.fasta --figure-width 9 --figure-height 12 --level-spacing 2 --node-spacing 2 --line-width 2
```

These presentation settings do not change scientific results. Each page is measured and fitted; large trees retain continuation pages. The viewer applies a bounded raster zoom and offers vector exports for closer inspection. See the [parameter map](docs/GUI_CLI_PARAMETERS.md) for ranges and preview limits, and the [maintenance assessment](docs/MAINTENANCE.md) for Python/MAFFT upgrade policy.

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

CI targets Python 3.9, 3.11, 3.13, and 3.14 on Linux, with application type checks and strict configuration/layout checks. It requires exact **100% statement and branch coverage of `src/flutrees`**, unchanged from the prior release. Tests include 30 frozen legacy tree hashes, 12 differential legacy/current CLI runs, independent position-level oracles for all modes, 5,000 Hypothesis-generated datasets and uncertainty masks, JSON reload/round trips, a real Excel worksheet-boundary test, real MAFFT, reference/error cases, interruption and missing-artifact failures, workbook/PDF contents, paginated figure geometry, native Graphviz rendering, a desktop example under Xvfb, Chromium report checks, and fresh-wheel execution.

Coverage measures executed code, not scientific validity or absence of all defects. MAFFT, Tk, third-party libraries, installation helpers, and release tooling are outside the Python application coverage denominator. See [the acceptance matrix](docs/ACCEPTANCE.md) and [v0.3.2 validation scope](docs/VALIDATION_0.3.2.md). Release packages include the completed run's actual installer transcripts, benchmark measurements, test report, and coverage data. The [v0.3.0 validation record](docs/VALIDATION_0.3.0.md) is retained as historical documentation.

For the complete local checklist and GitHub publication sequence, see the [maintainer test and release procedure](docs/MAINTAINER_RELEASE.md).

MIT License. See [LICENSE](LICENSE) and [CITATION.cff](CITATION.cff).
