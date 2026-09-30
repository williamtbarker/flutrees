# FluTrees 0.3.2 validation scope

## Change boundary

This release upgrades the native GUI, strengthens shared input validation, and adds five optional flat presentation fields and CLI flags. Existing analytical defaults, alignment execution, mutation calling, split strategies, pruning, scientific tree/table schemas, and output folder layouts retain the 0.3.1 contracts. Tree figures intentionally gain measured fitting and adjustable aspect/spacing/stroke. Configuration records include the new presentation fields; analytical fingerprints exclude them. Package version and version-dependent fingerprints necessarily change relative to 0.3.1.

The implementation map and fixed-policy audit are in [GUI_CLI_PARAMETERS.md](GUI_CLI_PARAMETERS.md). The scientific, installer, benchmark, and publication requirements described in [VALIDATION_0.3.1.md](VALIDATION_0.3.1.md) and [ACCEPTANCE.md](ACCEPTANCE.md) continue to apply. Their historical release references describe 0.3.1; a 0.3.2 kit must carry its own evidence.

## Desktop and command-line acceptance

- Compare all eleven existing configuration fields, selected inputs, output directory, and explicit run name between GUI and CLI across all four tree selections and all three alignment-profile choices. Separately round-trip all five new presentation fields.
- Preserve default `RunConfig` values, timestamp-based GUI names, CLI SLURM names, and automatic thread selection.
- Reject invalid whole-number fields, invalid/nonfinite frequency, out-of-range values, blank MAFFT, nonportable run names, and existing run folders before starting a worker or creating outputs.
- Verify file addition/deduplication, removal, clearing, example loading, running-state guards, locked/restored widgets, and successful/failed worker handling.
- Check shell quoting using paths and references containing spaces, quotes, and shell metacharacters. Round-trip copied POSIX commands through the actual CLI parser; validate PowerShell quoting separately.
- Under a real Tk display, execute the bundled example with defaults and with non-default depth/count/frequency/pruning/thread/alignment/tree-mode/run-name settings. Run the equivalent CLI configuration separately using real MAFFT, and compare each mode's full/pruned tree JSON and assignments byte-for-byte.
- Verify actions remain reachable in the desktop; resize and inspect the Analysis, Advanced, Tree viewer, and Run log surfaces. Scrollable settings retain access at the minimum window size.
- Check runtime types through the Python API, nonfinite/huge inputs, broken clipboard, worker startup failure, malformed/incomplete/oversized saved data, invalid-layout recovery, repeated Tk lifecycles, and CLI imports without Tk.
- Exercise root-only, asymmetric, deep, and paginated trees; test extreme aspect ratios/gaps with complete node-box bounds and non-overlap. Verify bounded viewport allocation, page navigation, fit/zoom, native resize settling, and PNG/SVG/PDF export with retained SVG text.
- Change only layout and require unchanged analytical identity plus byte-identical JSON/assignments across all modes. Verify requested dimensions in primary/alternative tree PDFs and the report's tree pages.

## Evidence and limits

Development validation and release validation use separate evidence. The completed release kit's `BUILD_INFO.txt` identifies the source commit and CI run. Its test report and coverage counters must come from that run, alongside the installer and performance evidence; historical measurements must not be relabeled as current validation.

Linux desktop checks do not certify native macOS/Windows rendering, Tk availability, clipboard behavior, or installer paths. A session log is not a persistent run database. Activity indication does not estimate completion time. The close guard is not subprocess cancellation. Settings are captured before worker launch; the analysis engine remains responsible for input/reference/executable preflight, exclusive run creation, completion status, and output manifests.

## Development validation — 2026-09-30

Baseline: `v0.3.1`, commit `5615de9779c9ebaa27131f5400999951f36226c1`. Review findings are recorded in [REVIEW_0.3.2.md](REVIEW_0.3.2.md); servicing recommendations are in [MAINTENANCE.md](MAINTENANCE.md).

| Check | Observed result |
|---|---|
| Full application suite, Linux Python 3.12.14 / MAFFT 7.505 | 261 passed in 167.07 seconds; zero failures, errors, or skips. Includes real MAFFT, native Tk under Xvfb, Graphviz, twelve legacy CLI differential cases, generated strategy cases, and the actual Excel row boundary. |
| Exact statement and branch coverage | All 1,664 statements and 506 branches covered; zero missing statements, missing branches, partial branches, or coverage exclusions. |
| GUI and layout checks | 60 GUI/theme/headless-import checks and 87 layout/type/invariance checks, also included in the full suite. The native cases run analysis, compare real CLI results, inspect tree fitting, change layout, preview page aspect, and close successive windows. |
| Scientific presentation invariance | Changing only style preserves the analysis ID and all modes' full/pruned tree JSON and assignment bytes. Primary/alternative tree PDFs and report tree pages reflect the requested page dimensions. |
| Static checks | Ruff, application-wide mypy (19 modules), strict mypy for configuration/layout, and `git diff --check` passed. Dynamic Tk and untyped third-party boundaries remain documented limitations. |
| Wheel/source distributions | Both 0.3.2 distributions built successfully; packaged Python files were checked against the source tree. |
| Installed-wheel execution | Imported the wheel from a separate virtual environment's site-packages outside the source directory. Completed a 48-record synthetic all-view run with custom thresholds and a 24-record public-HA all-view run; both used custom spacing/stroke and 9 × 12 inch tree pages. Shared runtime dependencies were available in this environment; isolated installer qualification remains a CI gate. |
| Native visual review | Inspected Analysis, Advanced, Run log, and the fitted Tree viewer; viewer controls remain reachable at 1000 × 820 and 860 × 620. The real tree fits its viewport; Whole page previews the actual printed aspect and margins. Saved pre-layout runs load successfully. |

This development run does not cover the separate browser job, isolated README installers, workload benchmarks, or Python version matrix. Publication requires successful release CI on the published commit: Python 3.9/3.11/3.13/3.14, browser checks, three installers, six workload sizes, alignment repetitions, and verified Test Kit packaging. Native Windows/macOS acceptance and MAFFT 7.526 qualification are not established by this Linux/MAFFT 7.505 record. See [MAINTAINER_RELEASE.md](MAINTAINER_RELEASE.md) for the local acceptance and publication procedure.
