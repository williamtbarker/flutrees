# Adversarial review — 28 September 2026

Scope: scientific coordinate integrity, hostile/malformed input, record identity, tree partitions, export completeness, interruption behavior, and readable results. Baseline: v0.2.0 (`f14643a`). Fixes: v0.2.1.

## Reproduced defects and corrections

| Finding | Evidence from the baseline | Correction and regression |
|---|---|---|
| Silent residue loss could produce wrong mutation labels | Real MAFFT removed `?` from `AC?DEFGHIKLMNPQ`; a known F6Y change became F5Y. It also removed `*`, which the input validator accepted. | Preserve `?`, `U`, and `O` as X with recorded QC. Remove one terminal stop, reject internal stops. Real MAFFT regression asserts F6Y and unknown position 3. Alignment must preserve every extracted non-gap residue. |
| Pre-gapped inputs mixed alignment columns with residue coordinates | At window 3–5, `AC-DEFG` extracted `-DE` while the corresponding ungapped protein extracted `DEF`. | Reject pre-gapped input before creating results; explain that unaligned proteins are required. Do not silently remove gaps and reinterpret supplied coordinates. |
| Long FASTA identifiers failed the otherwise valid analysis | MAFFT truncated a 500-character ID. | Compact transport IDs protect the aligner input. Restore complete public IDs and original order before selecting the reference. Real MAFFT and workbook tests verify a 510-character ID is retained. |
| Exact frequency boundaries could reject eligible branches | Binary floating-point evaluation of `ceil(0.07 * 100)` yields 8 rather than 7. | Decimal evaluation preserves the requested threshold. Regression requires a 7/93 split at 0.07. |
| Malformed aligner output was insufficiently checked | Matching IDs alone cannot detect residue loss/replacement. Output reordering could alter a reference tie. | Reject residue loss, substitution, duplicated IDs, and unequal aligned lengths. Restore original input order independently of aligner order. |
| Completion checks omitted several advertised files | PNG/SVG and some TSV outputs were outside the required-artifact gate. | Require overview figures, tables, and intermediate FASTA files as well as PDF/Excel/HTML. Deleting a figure during export must leave failed status. |
| Interrupted runs retained an ambiguous running state | KeyboardInterrupt bypassed Exception handlers. | Record failed status and an interruption explanation at dataset and run level. Forced process termination still cannot guarantee status updates. |
| Pruned groups lacked consistent stopping explanations | HTML inferred a pruning explanation, while JSON and workbook stopping reasons remained empty. | Attach an explicit hidden-record explanation to the pruned node without altering the full tree. |
| Workbook creation errors could escape CLI error presentation | XlsxWriter FileCreateError is not an OSError. | Display the actionable error through the normal CLI failure path. |
| Wholly unknown windows and short references were insufficiently distinguished | Unknown-only windows passed initial validation; a short modal reference could omit part of the requested comparison window. | Reject windows with no interpretable amino acids; explicitly disclose short selected references and excluded reference-gap positions. |
| Provenance could describe a different file from the one analyzed | The original file was hashed after alignment; an edit during a run would change the reported checksum without changing extracted data. | Analyze an exact retained input snapshot and hash those same bytes. A regression changes the source file during alignment and checks both snapshot and checksum. |

## Validation

- Exact package statement and branch coverage remains required, without excluding new code or weakening the threshold.
- 100 deterministic randomized datasets are checked against an independent per-position observation oracle. Assertions cover membership conservation, positive/negative partition correctness, minimum counts, exact rational frequency limits, depth, and uncertain observations. More than 100 actual splits are exercised.
- Fault injection verifies failures before publication and correct run/dataset statuses.
- Real MAFFT runs cover the bundled 48-record example, the existing 24-record public HA fixture with independently established expected mutation counts, long identifiers, unknown residues, and a short modal reference.
- Existing PDF, SVG, workbook, browser, desktop, and clean-wheel checks remain required. CI runs Python 3.9, 3.11, and 3.13 on Linux; the local environment runs Python 3.12. Native display checks execute in CI under Xvfb.

## Remaining limits

This review does not establish clinical validity, phylogenetic meaning, standardized HA numbering, or representativeness of the public fixture. Input sequences must share a meaningful starting convention and be translated proteins; sequence letters alone cannot always distinguish protein from nucleotide input. Reference-gap columns remain outside the substitution-only analysis. Unknown observations deliberately withhold affected splits, which can reduce visible branching.

Native Windows/macOS installation and very large surveillance collections are not covered by this Linux test matrix. HTML and workbook generation materialize record membership and are not designed as streaming exports. A killed process or exhausted disk can prevent a final status update; only an explicit complete status indicates a finished run. The coverage metric measures execution; independent expected results and malformed-input tests check behavior but cannot rule out every defect.
