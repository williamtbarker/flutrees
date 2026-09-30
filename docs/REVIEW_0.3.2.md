# 0.3.2 adversarial review

Review date: 2026-09-30. Scope: all changes since the v0.3.1 baseline, with additional focus on GUI/CLI equivalence, presentation geometry, error recovery, runtime types, and future servicing. This is a source and behavior review backed by tests, not a guarantee that no defects remain.

## Findings addressed

| Finding | Consequence | Correction and evidence |
|---|---|---|
| Python accepts `bool` as an `int`; unchecked float/string configuration could cross API boundaries. | Scientifically meaningful counts/depths could receive unintended values or produce inconsistent errors. | Exact integer validation for depth, residue bounds, split/prune counts, and threads; finite, non-Boolean frequency/style validation; malformed mode, reference, executable, and run-name types rejected. Adversarial tests include NaN, infinity, huge integers, strings, lists, and Booleans. |
| Width/height changes alone did not guarantee label fit or useful node gaps. | Portrait, short, deep, or crowded figures could clip or overlap. | Measure labels before layout, allocate gaps around measured envelopes, retain equal-axis geometry, and shrink uniformly only when needed. Tests check complete node-box and decoration bounds, non-overlap, extreme page sizes/spacings, root-only trees, asymmetric pruning, and depth-20 trees. |
| A fitted print page could make the tree too small in the desktop because of blank margins. | Poor initial readability, particularly for small trees. | The desktop fits the actual tree bounds with padding; Whole page previews the page aspect and margins, while export keeps the full page. Fit limits native enlargement to 2x for small trees. Relative zoom spans 25–800% of fit with an eight-million-pixel/8,000-axis cap. |
| Unbounded viewport enlargement or whole-tree display could consume excessive memory. | Frozen or failed desktop inspection on large data/screens. | Rasterize one continuation page at a time; preserve four-level pagination and all branches. Reject saved tree JSON above 64 MiB and metadata above 1 MiB. Property tests exercise 250 viewport/zoom cases in addition to explicit boundary failures. |
| Invalid layout after navigation could leave the preceding figure available to export. | A saved page could differ from the selected page. | Clear failed previews and disable zoom/save until rendering succeeds. Regression checks cover navigation, failure, correction, and successful export. |
| Saved-run metadata could be a list, incomplete status, invalid JSON, or excessively nested data. | Callback exceptions instead of a usable error; incorrect completion assumptions. | Require a completed object status, validated tree structures, recognized full/pruned files, and paths resolved within the run. Handle file/JSON/recursion failures without starting analysis. |
| Clipboard or worker startup could fail. | An uncaught callback or permanently locked controls. | Show actionable errors; restore controls and log startup failures. No output directory is created by validation or command copying. |
| Pending callbacks and Tk reference cycles could survive a closed window. | A reproduced native Tk failure during garbage collection in a subsequent analysis worker. | Cancel scheduled callbacks, release viewer images/figures and bound callbacks, and collect old Tk cycles on the GUI thread before worker launch. Native tests create, analyze, inspect, and close multiple desktop instances in one process. |
| Newly imported ImageTk could inadvertently require Tk for CLI imports. | Headless installations could stop working. | Keep ImageTk import inside drawing. A fresh subprocess deliberately blocks all Tk imports and verifies CLI version handling plus the explanatory GUI error. |
| Presentation fields could enter scientific fingerprints. | Restyling could imply a different scientific analysis. | Record the fields in configuration but exclude them from analytical identity. End-to-end tests compare all three modes: unchanged analysis ID, byte-identical full/pruned JSON and assignments, changed image output, and the requested PDF page dimensions. |
| Static checks exposed mixed row types and optional renderer state. | Misleading type assumptions could conceal defects during later servicing. | Add explicit mixed-data types, optional viewer state, concrete Agg canvases, and typed configuration/layout boundaries. CI checks the complete application and applies strict checks to the pure validation modules. |

## Compatibility and exactness

Existing scientific defaults, alignment profiles, mutation calling, uncertainty handling, split eligibility/ranking, node membership, and full/pruned JSON schemas are preserved. The flat configuration gains five presentation fields; existing positional fields retain their order. CLI options are additive. Figure geometry intentionally changes; scientific results must not.

The frequency threshold continues to use its existing exact-decimal rule. Type validation does not replace that computation. The existing pinned legacy differential suite, generated strategy oracles, conservation checks, reference tests, and export boundary checks remain release requirements. No coverage exclusions or thresholds were introduced to accommodate new code.

GUI state is captured before the worker starts. Render/save/select actions are disabled while analysis runs, avoiding simultaneous Matplotlib operations. Resize and zoom operate only on the cached image. Explicit Figure/Agg canvases avoid registering preview figures in pyplot's global window registry. SVG page exports preserve text elements.

The launcher remains a native Tk adapter to the shared pipeline. Page width/height, level/node spacing, and branch weight flow through the same configuration to GUI runs, copied CLI commands, primary and alternative tree figures, and tree pages in the PDF report. Fit resets on tree/page/layout changes; ordinary resizing preserves zoom relative to the fitted viewport. Field validation and page bounds are verified independently of screenshots.

## Remaining limits and release gates

See [VALIDATION_0.3.2.md](VALIDATION_0.3.2.md) for observed local results and checks still required from the actual release CI commit. Native Linux rendering does not establish native macOS/Windows acceptance. Static checking of dynamic Tk and third-party APIs is necessarily weaker than the strict pure configuration/layout checks. Coverage does not measure every operating-system error or prove scientific correctness.

The viewer reads the current GUI layout when opening saved data; it does not import historical analysis settings. Single-page export writes the displayed layout and is separate from regenerating every output or updating a run manifest. A saved tree larger than the preview limit needs its complete paginated PDF or another data inspection workflow. Arbitrarily large trees cannot all be legible on one screen; pagination, fit, and bounded zoom provide complete navigation within the supported input limits.

The [maintenance assessment](MAINTENANCE.md) covers servicing, deployment baselines, qualification, and rollback.
