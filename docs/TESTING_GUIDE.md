# FluTrees 0.3.2: installation and testing

Start with the included example, then try one small protein FASTA you know well.

## 1. Preview the finished outputs without installing

If you downloaded the test kit, unzip it and open **START_HERE.html**. The example reports are already generated. Open a PDF tree, its `.txt` trace, and the Excel workbook. Keep the whole folder together so the report links work.

The synthetic example contains 48 records in four deliberately constructed groups. It is a software demonstration, not a biological reference panel. The public HA example contains 24 protein records; its provenance and independently established expected counts are included under `example_inputs`.

## 2. Install on your computer

Requires Python 3.9 or newer and MAFFT. Installation downloads Python dependencies; subsequent analysis and report viewing run locally. MAFFT is a separate program and is not bundled in the wheel.

On macOS, check the prerequisites in Terminal:

```bash
python3 --version
mafft --version
```

If MAFFT is missing and Homebrew is already installed, run `brew install mafft`. Do not repeat that command if MAFFT is already available. A missing Tk installation affects only the optional desktop window; the command-line workflow still works.

For the downloaded test kit, run these commands after opening Terminal in the extracted kit folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install package/flutrees-0.3.2-py3-none-any.whl
flutrees --version
flutrees --demo --open
```

The version should be **0.3.2**. Terminal will show progress and the results path; your browser should open the overview. Results go into a new folder under `runs` and never overwrite an earlier run.

If working from a GitHub source download instead, run `python -m pip install .` from its project folder in place of the wheel-install command. The other commands are the same.

On Windows, use `py -m venv .venv` and `.venv\Scripts\activate` in Command Prompt, then the same `python -m pip` and `flutrees` commands. Install a compatible MAFFT executable and add it to PATH. Automated installation tests run on Linux; check the example on Windows or macOS before analyzing laboratory data.

## 3. Test the desktop window and your own data

With the environment still activated:

```bash
flutrees --gui
```

On **Analysis**, click **Use included example**, choose a results folder, then **Analyze sequences** and **Open results**. The file table supports adding and removing individual datasets. **Advanced** contains MAFFT, threads, and alignment choices; **Run log** retains progress and submitted commands for the current session.

After a default example succeeds, use a new Run ID and try Max depth = 1, Min split = 2, Min freq = 0.25, and Prune cutoff = 20. Select Tree view = all. Confirm these values in `summary.json` and the workbook Parameters sheet; all full trees must stop at depth 1. The frequency value is a fraction (0.25 = 25%), applied to each parent node. The pruning cutoff affects only simplified trees. Entering 5% or a depth above 20 should produce an error before analysis begins.

Use **Copy CLI command** to inspect the equivalent invocation. It does not run anything. Commands target POSIX shells on macOS/Linux and PowerShell on Windows. A blank Run ID produces a new timestamp on each copy or analysis; use an explicit name if the exact folder name matters. Reusing a completed name must preserve the old run and ask for a new name.

Resize the window and scroll Analysis as needed. Analyze/status/Open results must remain visible. During a run, fields should lock, progress should appear in Run log, and completion should unlock controls. Next, choose one of your own small, unaligned amino-acid FASTA files. Check the residue window against that input's starting convention. The default is **84-284 inclusive**.

The command-line alternative is:

```bash
flutrees -i /path/to/your_proteins.fasta --open
```

Use translated, unaligned proteins with consistent starting positions. Existing `-` alignment gaps are rejected. An internal `*` stop needs checking; a single terminal stop is removed and recorded. This software does not infer HA numbering conventions or automatically translate nucleotide input.

In **Tree viewer**, choose each available full/pruned tree. Try Width = 9, Height = 12, Level gap = 2, Node gap = 3, and Line width = 2.5, then **Apply layout**. The tree should fit completely, with separated labels and branches. Enable Whole page to inspect the selected page aspect and print margins. Zoom in, drag to pan, then **Fit**. Change page on a large tree and confirm that zoom resets; all continuation pages remain accessible. Use **Save page** to export a new PNG/SVG/PDF outside the run folder. Reopen a completed run with **Open saved run** and repeat without realignment. Settings entered before a new analysis must appear in its configuration and tree exports; presentation changes must not change tree JSON or assignments.

Try a root-only tree (Max depth = 0), a deeper tree, portrait/landscape pages, and the minimum window size. Enter a nonfinite layout value such as `nan`: it must show an error and disable saving a stale preview. Fit/zoom are bounded for desktop memory; extremely large saved JSON should give a clear limit message and leave complete PDF exports available.

## 4. What a successful test looks like

- The run ends with **Complete**, states **Your output is X files**, gives the absolute folder path and key output filenames, and its status file says `complete`.
- `report.pdf` contains the summary, mutation chart, and a branching tree diagram.
- `tree_full.pdf` and `tree_pruned.pdf` show readable nodes and edges. Large trees continue onto numbered pages.
- `tree_full.txt` traces every node with indentation; the simplified trace explains hidden groups.
- `results.xlsx` opens with seven sheets. In Records, filter `full_group_id` to select a terminal group; `full_group_path` shows all decisions. Group IDs can change between runs.
- The HTML tree expands and collapses; its links open the expected files.
- For the synthetic example, mutation counts are **12, 12, and 24**, and the first split is **24/24**. There are four final groups of 12 records each.
- For your own data, inspect a few known sequences against the recorded reference and confirm that the numbering matches your intended interpretation. A mutation decision tree is not a phylogeny.

The first PNG/SVG is the overview; `_page_002` and later files contain continuation pages. Use the complete PDF or text trace when inspecting a large tree. DOT files are optional editable graphs for Graphviz users.

## 5. If anything is confusing or fails

Keep the results folder. Share the exact message, installed version, operating system, and the relevant `status.json` or `mafft.log`. For a visual problem, a screenshot of the affected page helps. Use a non-confidential example when sharing inputs or outputs.

When reporting a usability problem, identify the step involved: selecting files, choosing the residue window, opening a PDF, or filtering records in Excel. Include the expected behavior and what happened instead.


## Tree-family acceptance checks

Run `flutrees --demo --tree-mode all --threads 1 --open`. Confirm frequency, balanced, and diversity directories under `trees/`, a comparison section in HTML, and Tree Comparison / Tree Groups / All Membership sheets in Excel. Every mode must assign every input record to exactly one terminal full-tree group. Root-level tree files mirror frequency for this command.

Check `provenance.json` for the MAFFT version, exact command including `--threadit 0`, alignment checksum, and analysis ID. Compare `method.json` in all three mode folders: all must refer to that same analysis ID. Do not expect the example's three views necessarily to differ; use the independent strategy tests for a deliberately discriminating fixture.

For your own data, `--reference-id` must identify exactly one original FASTA record. Repeat a small run into a different output folder with the same environment and settings; verify the alignment checksum and analytical fingerprint. This checks local repeatability, not cross-platform equivalence.

The README contains alternative conda/Miniconda and uv instructions alongside the original venv workflow. Choose one environment. Downloading an installer is not evidence of successful installation; verify both `mafft --version` and `flutrees --version` before analysis.

## Release acceptance evidence

The Test Kit includes `docs/ACCEPTANCE.md` and `docs/VALIDATION_0.3.2.md`, with the completed build's test report, coverage counters, full HA pipeline measurements, alignment comparisons, and exact README installation transcripts under `validation/`. Large workbook tables continue on numbered sheets; include those sheets when counting all records.

A default frequency-only run uses the historical alignment flags. An all-mode run uses reproducible refinement by default. To compare separate runs under the same alignment settings, explicitly pass `--reproducible` or `--legacy-alignment` to both. These choices are recorded in `summary.json` and `provenance.json`.
