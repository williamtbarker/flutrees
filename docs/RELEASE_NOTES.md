# FluTrees 0.3.2

Adds complete desktop parameter controls and an adjustable tree viewer. The GUI and CLI continue to use the same analysis pipeline.

## Added

- Editable Max depth, Min split, Min freq, Run ID, pruning cutoff, CPU threads, alignment profile, and MAFFT executable in the desktop.
- Analysis, Advanced, Tree viewer, and Run log tabs; file add/remove/clear controls; quoted CLI commands; persistent action and status controls.
- Tree page width and height, horizontal and vertical node spacing, and branch weight in both GUI and CLI.
- Saved-run inspection, continuation-page navigation, automatic fitting, whole-page preview, zoom/pan, and single-page PNG/SVG/PDF export without realignment.
- A GUI quickstart covering the included example, laboratory inputs, analysis settings, results, figure layout, and saved runs; setup instructions reuse working prerequisites.

## Fixed

- Node overlap and clipping at tested page-size and spacing extremes through measured label layout.
- Stale previews after invalid layout changes, clipboard and worker-start failures, malformed saved-run handling, and Tk cleanup between window lifecycles.
- Invalid Python API numeric inputs, including Booleans in integer fields and nonfinite frequency or layout values.
- Native desktop test selection on macOS and Windows; theme checks now cover native and fallback styles independently.

## Compatibility

Existing CLI flags, analytical defaults, alignment profiles, mutation rules, tree strategies, memberships, and scientific data schemas are preserved. Configuration records gain five presentation fields, excluded from analytical fingerprints. Figure appearance changes with the new fitting and layout controls.

Frequency-only runs retain historical alignment defaults; alternative/all views retain reproducible refinement. The complete parameter reference is in `docs/GUI_CLI_PARAMETERS.md`.

## Installation and validation

Download `FluTrees_v0.3.2_Test_Kit.zip`, extract it, and open `START_HERE.html`. Downloads also include the wheel, source archive, example PDF, and checksums. New analyses require Python 3.9 or newer and MAFFT; the desktop also requires Tk.

Publication requires the Linux Python 3.9/3.11/3.13/3.14 matrix, exact 100% application statement/branch coverage, static checks, real MAFFT, desktop/browser/export tests, installed-wheel execution, three installer checks, workloads through 25,000 records, and alignment comparisons. The Test Kit contains evidence from its actual release build. Native Windows/macOS acceptance is separate from Linux CI.

See `docs/MAINTAINER_RELEASE.md` for the testing and publication procedure, `docs/VALIDATION_0.3.2.md` for validation scope, and `docs/MAINTENANCE.md` for dependency servicing.
