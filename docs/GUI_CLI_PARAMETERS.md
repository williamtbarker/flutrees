# GUI and CLI parameter map

## Scope and design

Version 0.3.1 exposed all eleven `RunConfig` fields through the CLI, but only four in the desktop: residue start/end, tree view, and reference ID. Its desktop always generated a timestamp run name. Version 0.3.2 exposes the other seven configuration fields and an editable Run ID while preserving existing CLI option names, scientific defaults, pipeline behavior, and scientific data schemas. Five optional presentation fields extend the same flat configuration and CLI; their defaults retain the 14 × 8.5 inch tree page size.

The desktop remains a native Tk application. Analysis groups files, output location, and scientific settings; Advanced holds alignment/runtime options; Tree viewer provides layout, fitted inspection, and page export; Run log retains commands and progress for the current session. Actions and status remain visible when switching tabs or scrolling. The GUI is an adapter to `RunConfig` and `run_many`, not a second scientific implementation.

## Complete parameter inventory

| Setting | CLI | GUI location | Default and valid values | Effect |
|---|---|---|---|---|
| Input files | Repeated `-i` / `--input` | Analysis: Add FASTA files, file table, Remove selected, Clear | At least one unaligned protein FASTA | Each file is a separate dataset; records are not pooled across files. Adding the same resolved path twice keeps one entry. |
| Results folder | `-o` / `--outdir` | Analysis: Results folder / Browse | CLI: `runs`; GUI: `~/FluTrees_results` | Run and dataset folders are created beneath it. Existing behavior is retained. |
| Run ID | `--run-id` | Analysis: Run ID | GUI blank: timestamp; CLI omitted: SLURM job ID or timestamp | Names the enclosing run folder. Existing folders are never overwritten. Use a portable name such as `HA_2026_09_batch1`. Surrounding GUI whitespace is trimmed. |
| First residue | `--start` | Analysis: First residue | 84; integer at least 1 | Inclusive input-residue window start; also the reference coordinate offset. |
| Last residue | `--end` | Analysis: Last residue | 284; integer at least start | Inclusive input-residue window end; extraction precedes alignment. |
| Maximum depth | `--max-depth` | Analysis: Max depth | 10; integer 0–20 | Stops subdivision at this depth in every requested tree. Root depth is 0; zero produces only the root. |
| Minimum child count | `--min-split` | Analysis: Min split | 5; integer at least 1 | Both children must contain at least this many records. |
| Minimum child fraction | `--min-freq` | Analysis: Min freq | 0.05; finite fraction 0–0.5 | Both children must meet `ceil(fraction × current-node record count)`. This is not a percentage entry or a fraction of all inputs. |
| Pruning cutoff | `--prune-cutoff` | Analysis: Prune cutoff | 10; integer at least 1 | Hides smaller groups in simplified views; never changes full trees or their record assignments. |
| Tree strategy | `--tree-mode` | Analysis: Tree view | frequency; frequency/balanced/diversity/all | Selects the split ranking. All generates three views using the same alignment and observations. |
| Reference selection | `--reference-id`; `--reference auto` explicitly selects the default | Analysis: Reference ID | Blank: modal aligned sequence | An explicit original FASTA ID must occur exactly once in each selected dataset. Blank corresponds to auto; no duplicate auto selector is needed. |
| Aligner executable | `--mafft` | Advanced: MAFFT executable | `mafft`; executable name or full path | Locates MAFFT. The pipeline checks availability before creating the run folder. |
| CPU threads | `--threads` | Advanced: CPU threads | Blank/omitted: valid SLURM setting, otherwise 8; explicit integer at least 1 | Sets MAFFT threads. The equivalent command records the resolved number. |
| Alignment profile | `--reproducible` / `--legacy-alignment` | Advanced: Alignment profile | Mode default / Reproducible / Legacy | Mode default: frequency uses legacy, others use reproducible refinement. An override applies to every tree in the run. |
| Figure width / height | `--figure-width` / `--figure-height` | Tree viewer: Width / Height (in) | 14 × 8.5 inches; width 6–30, height 4–24 | Sets page dimensions and aspect ratio for tree figures, including tree pages in the report. |
| Horizontal level spacing | `--level-spacing` | Tree viewer: Level gap | 1; finite multiplier 0.25–4 | Changes the horizontal gap between measured node envelopes. |
| Vertical node spacing | `--node-spacing` | Tree viewer: Node gap | 1; finite multiplier 0.25–4 | Changes the vertical gap between node envelopes. |
| Branch stroke | `--line-width` | Tree viewer: Line width (pt) | 1.5; finite value 0.25–5 | Nominal branch width in points; scales down with the tree when necessary to fit a page. |

For example, a node with 101 records and Min freq = 0.05 needs at least six records in each child from the frequency threshold. If Min split = 10, both children must instead contain at least ten. Both requirements apply; zero frequency does not remove the minimum-count requirement.

## Workflow controls and operating behavior

| CLI or behavior | Desktop equivalent | Compatibility decision |
|---|---|---|
| `--demo` | Use included example | Replaces the selected inputs and resets the residue window to 84–284; retains other analysis settings. |
| `--open` | Open results | Enabled only after the current run completes. Browser failure shows the report path. |
| `--gui`; `flutrees-gui` | Desktop entry points | Both launch the same workspace with desktop defaults. CLI analysis flags alongside `--gui` are not a prefill mechanism. |
| `--version` | Version in window title/header | Same package version. |
| `--help` | Field units/ranges, Advanced explanations, this map | No existing CLI flags, aliases, or defaults are removed. |
| Terminal progress | Run log, status, activity bar | Indeterminate activity, not an invented percentage or ETA. Session log is in memory; analytical provenance, statuses, and MAFFT diagnostics remain on disk. |
| Repeatable invocation | Copy CLI command and logged submitted command | POSIX-shell quoting on macOS/Linux; PowerShell quoting on Windows. Copying does not execute. A blank Run ID produces a new name each time; repeating an existing run requires a different name. |
| Run in progress | Locked fields and file buttons | The worker receives a captured immutable configuration, copied input list, output path, and run name. Widget access stays on the GUI thread. |
| Invalid configuration | Field-specific error dialog | Rejects invalid values and existing run folders before starting the worker. Pipeline file/reference/executable preflight is retained. |
| Closing during work | Explanatory dialog | Preserves the existing close guard. No pretend cancellation of the subprocess/export pipeline. |

The portable-name validator is shared by GUI and pipeline, so desktop validation cannot relax the CLI/API naming rules. Folder creation remains exclusive in the pipeline, protecting against races after the GUI's early existence check.

## Internal policies intentionally kept fixed

The audit also traced non-configuration constants and rules in FASTA loading, metadata parsing, MAFFT invocation, mutation calling, split selection, tree rendering, exports, and provenance. These fall into two categories: scientific contracts and presentation/format limits. Exposing every constant as a control would change methodology or add low-value complexity.

| Internal rule | Why it stays fixed in 0.3.2 |
|---|---|
| MAFFT amino-acid/input-order/auto flags | Part of the tested alignment profiles. Arbitrary command flags, gap penalties, and strategy selection would require a separate scientific compatibility contract. |
| Input normalization, terminal-stop handling, rejection of internal stops/pre-gapped input, padding and duplicate-ID handling | Recorded data-integrity policies, not ordinary analysis settings. |
| Modal-reference tie order and substitution/reference-coordinate rules | Explicit reference selection already supplies the meaningful control. Insertions, standardized numbering, translation, or alternate mutation models would be new analysis features. |
| Uncertainty withholding at candidate positions | Prevents unknown observations being classified as confirmed negatives. A tolerance slider would change scientific meaning. |
| Record weighting, split eligibility, strategy tie-breaking, diversity rounding and site exclusions | Core tested definitions. No hidden random seed is used by the tree algorithms. Duplicate sequences remain separate observations. |
| Depth ceiling of 20 | Existing validated limit; allowing a higher ceiling is not required for exposing the parameter. |
| Top 25 substitutions in summary/chart; four tree levels per figure page; 140-DPI PNG export | Complete mutation tables, trees, memberships, and paginated exports remain available. Page dimensions, node gaps, and branch weight are now adjustable; bounded pagination and export resolution stay fixed. |
| Excel worksheet/cell limits, portable-name limits, transport IDs, schema/strategy versions and checksums | Format or integrity constraints, not useful scientist-adjustable controls. |
| `SLURM_CPUS_PER_TASK`, `SLURM_JOB_ID`, `SLURM_TMPDIR`, `MAFFT_TMPDIR` | Existing environment integration. Threads and run names have explicit overrides; temporary-directory placement remains an operational environment setting. |

All existing scientist-facing analytical parameters are accessible in both interfaces. New parameters for biological weighting, missing-data tolerance, alternative alignment methods are deliberately outside this usability patch.

## Tree inspection and presentation

After a completed run, open **Tree viewer** and choose the dataset/mode/full-or-pruned tree. **Open saved run** accepts a completed run folder from this or a previous version. It loads validated tree JSON and performs no new alignment. Layout fields use the current GUI values; opening a saved run does not silently import or overwrite analysis settings.

**Apply layout** measures labels and fits the current tree page's actual node bounds in the desktop, excluding blank print margins. **Fit** resets the zoom, with at most 2x native enlargement for small trees; **Zoom +/-** operate between 25% and 800% of fit, subject to a memory bound. Scrollbars and dragging pan enlarged pages. Fit is reestablished for each selected tree, page, and applied layout; resizing fits to the changed viewport at the current relative zoom. Large trees keep all branches across continuation pages rather than compressing the entire tree into one screen. Enable **Whole page** to preview the chosen aspect ratio, title, and print margins. Export always retains the full page dimensions, title, and explanatory text.

**Save page** exports the displayed page to PNG, editable vector SVG, or PDF without rerunning analysis. It saves one page, using the displayed layout; unapplied edits are not exported. Select a new destination to retain the original run's recorded outputs and manifests. Layout fields also apply to every tree figure generated by a subsequent GUI analysis. The same five CLI flags control batch exports. They do not alter HTML's expandable tree, the mutation-count chart, or DOT layout instructions.

Presentation values are recorded in configuration and workbook parameters, but excluded from analytical fingerprints. Changing only presentation preserves mutation observations, tree JSON, and group assignments. Integer scientific fields require actual integer types through the Python API; Booleans and float-like strings are not accepted. CLI/GUI text inputs are parsed before shared validation.

The preview rejects incomplete runs, malformed trees, tree JSON larger than 64 MiB, and status metadata larger than 1 MiB. Only one page is rasterized; viewport images are capped at eight million pixels and 8,000 pixels per axis. These are operational safeguards, not limits on scientific inference. Use complete paginated exports for larger saved trees.

## Verification design

Validation checks complete GUI/CLI configuration equivalence across four tree modes and three alignment choices, numeric and run-name rejection, file management, safe command quoting, control locking/recovery, small-window scrolling, saved-run handling, bounded zoom, extreme aspect/spacing geometry, and real desktop/CLI output equality with non-default settings. The unchanged scientific suite retains the legacy differential runs, independent strategy oracles, property-generated datasets, record conservation, and export boundary tests. See [0.3.2 validation scope](VALIDATION_0.3.2.md).
