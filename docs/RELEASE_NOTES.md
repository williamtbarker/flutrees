# FluTrees 0.3.0

Three complementary mutation-tree views from one HA alignment, with the original frequency split rule retained as the default.

## Download and start

Download `FluTrees_v0.3.0_Test_Kit.zip`, extract it, and open `START_HERE.html`. The kit includes the installable wheel, synthetic and public HA inputs, complete three-view example results, validation records, and checksums. Python 3.9 or newer and MAFFT are required for new analyses; neither is bundled. Existing reports can be viewed without installing FluTrees.

The wheel, source archive, example tree PDF, and `SHA256SUMS.txt` are also available separately. The README includes complete venv/pip, conda/Miniconda, and uv installation and run examples.

## Tree views

- **Frequency (Mode A, default):** retain the legacy most-prevalent eligible substitution rule and encounter-order tie handling.
- **Balanced (Mode B):** favor the most even eligible split.
- **Diversity (Mode C):** favor reduction in residue entropy at other completely observed positions, excluding the candidate's own site and its other alleles.
- **All:** `--tree-mode all` builds every view from the same alignment, reference, mutation calls, and uncertainty observations.

Each view has full and simplified PDF/PNG/SVG/DOT/JSON/text trees and record-level assignments. HTML and Excel expose cross-view comparisons. Root-level filenames remain available and mirror the primary view: frequency for `all`, otherwise the selected mode. Node and group IDs must be interpreted with their mode.

## Hardening and usability

`--reference-id` selects one unique original FASTA ID; modal reference selection remains the default. MAFFT uses `--threadit 0` by default to avoid multithreaded iterative-refinement variation; `--legacy-alignment` restores the previous flags. Provenance includes software versions, the exact alignment command, content checksums, and an analysis fingerprint. Unsafe output names are normalized with collision checks. Completion requires every requested view and continuation image.

The desktop window includes tree-view and reference controls. The CLI reports selected modes, file count, absolute output location, and which report to open. Existing input-integrity, uncertainty, snapshot, and failure-reporting protections remain in place.

## Validation and interpretation

Release publication is gated on Linux tests for Python 3.9, 3.11, and 3.13; exact 100% application statement and branch coverage; legacy golden outputs; independent strategy oracles and property tests; real MAFFT and desktop checks; Chromium and Graphviz checks; and fresh-wheel example runs. Benchmark scope and limitations are documented in `docs/VALIDATION_0.3.0.md`.

These are exploratory mutation decision trees, not phylogenies, confidence estimates, or clinical interpretations. The frequency split rule is unchanged for identical mutation observations; altered alignment settings, references, inputs, or software versions can change upstream observations. Native Windows/macOS desktop installation and large-scale end-to-end surveillance workloads are not certified by this release.
