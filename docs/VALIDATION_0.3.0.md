# FluTrees 0.3.0 validation scope

## Compatibility and scientific behavior

`tests/data/frequency_023_golden.json` contains 30 canonical tree hashes generated with the v0.2.3 implementation at commit `5683105e015e19ccaa5744789de9ad8941331975`. It records the source hash, deterministic observation seeds, and parameters. These hashes cover topology, node IDs, membership, labels, and stopping reasons. Both default and explicitly selected frequency modes must match them. This tests the split rule on identical mutation observations, not equality between different MAFFT alignments.

The strategy test suite independently reconstructs residue categories and eligible candidate partitions. It checks the winning split against an independent entropy implementation rather than reusing production scoring. Five hundred Hypothesis-generated matrices exercise all three modes, complete observations and uncertainty masks, deterministic ties, record conservation, disjoint children, exact rational frequency thresholds, depth, and non-mutating pruning. A constructed population requires three different root decisions: frequency, balance, and cross-position diversity are not aliases.

Diversity uses categorical residue entropy with one weight per position. The candidate's entire site is excluded, and incomplete sites are excluded consistently across candidates in a node. This avoids giving a candidate credit for predicting itself or its mutually exclusive alleles. It is not a biological-effect estimator.

## Integration and output contracts

Tests include the original real-MAFFT synthetic and public HA fixtures, known expected substitution counts, unknown normalization, long identifiers, malformed aligner output, and reference selection. Family tests require one alignment call, identical shared provenance across modes, complete record assignments, valid local HTML links, readable workbook/PDF outputs, and explicit failure when a required family artifact disappears.

Existing PDF pagination, figure geometry, text/DOT topology, native Graphviz, desktop/Xvfb, browser/Chromium, clean-wheel, and interruption tests remain. CI requires zero missing statements and zero missing branches in every `src/flutrees` module. No coverage exclusions or reduced thresholds were introduced.

## Tree-construction benchmark

Run:

```bash
python benchmarks/benchmark_tree_modes.py --output benchmark.json
```

The recorded measurements are in `docs/benchmark-results-0.3.0.json`. The fixture contains 12 synthetic variable positions with complete observations. Parameters are depth 6, minimum child count 5, and minimum child fraction 0.05. Input sizes are 100, 500, 1,000, 5,000, 10,000, and 25,000 records. Each mode is measured separately; timestamps cover tree construction, not input generation, alignment, or exports.

On the recorded Linux/Python 3.13.5 environment, the 25,000-record measurements were approximately 0.70 seconds for frequency, 0.66 seconds for balanced, and 0.88 seconds for diversity. These are single-run development measurements, not service-level targets. More variable sites, deeper trees, different hardware, and record-rich output generation can cost substantially more. The benchmark does not establish capacity for 25,000-record end-to-end HA analyses.

## Known boundaries

No clinical, antigenic, phylogenetic, or standardized HA-coordinate validity is implied. Users must verify translation, shared input numbering, selected window, reference, and QC notes. Changing alignment flags, versions, references, or input ordering can change the observations or tie behavior. A content fingerprint does not certify an analysis.

Native Windows/macOS desktop installation is outside the Linux CI matrix. Installation commands are platform-specific. Excel sheet-size limits and in-memory HTML/workbook membership expansion constrain very large outputs. There is no streaming export or claim of arbitrary surveillance-scale performance. Forced termination or exhausted storage can prevent final status writes; only an explicit complete status indicates success.
