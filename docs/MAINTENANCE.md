# Maintenance and dependency servicing

Assessment date: 2026-09-30. This is an engineering assessment and proposed servicing policy, not a claim that future dependency releases are already compatible.

## Overall assessment

FluTrees is maintainable as a small scientific desktop/CLI application. Both interfaces use one immutable configuration and one analysis pipeline. Alignment, mutation observations, tree strategies, rendering, and exports have separate modules. Existing independent scientific oracles, legacy differential tests, provenance, exclusive output creation, and release gates provide useful protection against regressions.

The main ongoing cost is validating the environment around the application: Python, its scientific packages, the external MAFFT executable, and platform-specific Tk behavior. A successful installation or passing import test does not establish scientific equivalence after an upgrade. Keep one validated laboratory environment unchanged while evaluating updates in a separate environment.

## Dependency and platform risks

| Component | Failure or drift to watch for | Servicing response |
|---|---|---|
| Python and packaging | Older interpreters lose upstream support; new versions may initially lack compatible dependency wheels. Build tooling and installer bootstraps also change. | Keep the current patch release's Python >=3.9 compatibility contract, but do not choose 3.9 for a new managed deployment. Qualify a supported stable Python version with the complete release gates and the customer's OS. Plan minimum-version changes in a separately documented release. |
| MAFFT | Changes in alignment can change reference choice, called substitutions, and every resulting tree, even when FluTrees code is identical. Distribution packages can lag upstream. | Record and retain the exact executable version/build and command; validate replacement binaries against the previous approved environment before use. Check the alignment and observation checksums before comparing tree outputs. |
| Biopython and pandas | Parser behavior, data types, missing-value handling, and dependency minimums can change. | Keep FASTA normalization, duplicate/long-ID, coordinate preservation, uncertainty, exact threshold, and independent strategy tests. Investigate changed observations rather than regenerating expected outputs to silence tests. |
| Matplotlib and Pillow | Font metrics, backend behavior, image APIs, or supported Python versions can change. | Check measured node bounds, non-overlap, pagination, PDF dimensions, PNG/SVG export, and native resize/zoom. Allow harmless file-byte differences only after visual and data review. Pillow is now a declared direct dependency because the viewer uses it. |
| Tk and operating systems | Theme scaling, high-DPI screens, clipboard, file dialogs, image lifetimes, and thread finalization differ by platform. | Maintain customer-platform smoke checks for open/save, minimum window size, repeated runs, close/reopen, error recovery, and zoom/pan. Linux/Xvfb coverage alone does not certify native Windows or macOS. |
| Typer, XlsxWriter, report consumers | Command parsing, workbook restrictions, or rendering behavior can change. | Retain copied-command round trips, real Excel limits, PDF inspection, offline browser checks, and installed-wheel execution outside the checkout. |

As checked on the [Python lifecycle page](https://devguide.python.org/versions/), Python 3.9 reached end of life on 2025-10-31; 3.10 is scheduled to reach end of life in October 2026. Python 3.13 and 3.14 are in bugfix support; 3.11 and 3.12 are in security support. Version 0.3.2 adds Python 3.14 to the existing Linux CI matrix of 3.9, 3.11, and 3.13. Release approval requires every matrix job to pass. The separate development validation record uses Python 3.12.14.

The [MAFFT upstream page](https://mafft.cbrc.jp/alignment/software/) currently advertises 7.526. The local checks used 7.505; compatibility with 7.526 has not been established by those checks. Upstream documents a historical bug affecting `--auto` in versions 7.463–7.486 and advises 7.487 or later. Use that as a deployment floor, while retaining an explicitly validated MAFFT build for reproducibility. Do not silently replace an existing laboratory executable.

[MAFFT's threading documentation](https://mafft.cbrc.jp/alignment/software/multithreading.html) explains that multithreaded iterative refinement can vary across runs and that `--threadit 0` disables threading for that stage. FluTrees retains its explicit alignment profiles. The reproducible profile is not a promise of identical outputs across different MAFFT releases, machines, or changed input order.

## Practical service cadence

| Trigger | Work and acceptance |
|---|---|
| Monthly review | Inspect dependency/MAFFT release notes, security notices, failed CI, and customer issues. Prioritize relevant defects; review does not imply automatic production upgrades. |
| Quarterly dependency refresh | Resolve dependencies into a separate environment, save the resolved versions and MAFFT build identity, run the scientific/UI/export gates, and perform the customer-platform smoke test. Promote only a passing, reviewed environment. |
| New Python minor version or MAFFT version | Treat as a qualification event. Compare alignment, mutation observations, references, topology, memberships, report semantics, and resource use on the bundled examples plus a representative, non-confidential laboratory fixture. Explain every scientific difference before approval. |
| Security or data-correctness defect | Triage promptly outside the quarterly cadence. Reproduce, add a regression test, patch, rerun affected scientific gates plus release acceptance, and document whether old analyses need reevaluation. |
| Each release | Produce immutable wheel/source artifacts and a Test Kit tied to the actual CI commit. Retain installer transcripts, coverage counters, workload results, alignment comparisons, and rollback instructions. |
| Annual support review | Revisit supported Python and OS versions, installer availability, service expectations, and whether customer workflows require stronger native-platform automation. |

For planning, budget roughly 2–4 engineer hours per month for review/triage, an additional 4–8 hours for a routine quarterly qualification, and 1–3 engineer days for a significant Python/OS/MAFFT migration. These are estimates for the current scope, not measured costs or a service guarantee; scientific differences, platform incidents, and feature work can exceed them.

## Environment control and rollback

1. Preserve the working environment's Python/platform identity, resolved Python packages, MAFFT version/build, and FluTrees wheel checksum. A `pip freeze` snapshot is platform-specific and does not capture MAFFT or system Tk; keep those records separately.
2. Build the candidate in a separate environment. Use a supported Python release for new managed deployments and qualify its actual dependency resolution. The broad lower bounds in `pyproject.toml` are compatibility declarations, not a tested lockfile for every future version combination.
3. Compare against the prior approved environment using identical inputs, explicit alignment profile, reference, threads, and analytical settings. Presentation settings do not enter the analytical identity, but remain recorded in the configuration.
4. Review differences and retain both environments until acceptance. Roll back by invoking the previous environment/executable and writing a new run folder; never overwrite old results.

Avoid speculative upper bounds on every library. Add a targeted constraint when a demonstrated incompatibility requires one, with a regression test and removal condition. A curated deployment constraints file can supplement the portable package after it has been validated on the intended OS.

## Maintainability changes in 0.3.2 and remaining work

`layout.py` centralizes validated presentation settings and viewport limits; `gui_viewer.py` separates inspection/export from the launcher. One measured renderer supplies GUI pages and tree PDF/PNG/SVG exports. No separate tree inference or alignment implementation was introduced. GUI rendering/export is disabled during analysis because [Matplotlib is not thread-safe](https://matplotlib.org/stable/users/faq.html); resize and zoom use the cached image. Tk operations and cleanup stay on the main thread.

CI now checks application types with mypy and applies strict checking to configuration/layout boundaries. Tk widgets, dynamically constructed GUI fields, and parts of the older pipeline still use dynamic types. Passing these checks is not a claim of strict typing throughout the application. Runtime validation rejects Booleans in integer/fraction fields, nonfinite values, malformed configuration, and unsafe run names.

The next useful investments are native customer-OS smoke automation and a versioned, platform-specific deployment baseline. If saved profiles, cancellation, or interactive topology editing are later requested, extract more GUI state into a typed controller before adding those features. They are not prerequisites for the current release. The existing close guard deliberately waits for analysis completion; no cancellation system or automatic background updater is claimed.

Large trees remain paginated, with at most fifteen visible nodes per page and a fit reset on selection, page changes, or layout changes. Desktop tree loading is limited to 64 MiB JSON; cached viewport rasters are limited to eight million pixels and 8,000 pixels per axis. These bounds protect interactive use; they do not make an arbitrarily large tree legible on a single screen. Complete paginated exports remain the appropriate fallback.
