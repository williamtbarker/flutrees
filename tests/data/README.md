# Public HA integration fixture

Downloaded from NCBI Protein on September 28, 2026 using ESearch/EFetch.
Query: `Influenza A virus[Organism] AND hemagglutinin[Protein Name] AND H3N2[All Fields] AND 2019[All Fields]`, first 24 results.

Source: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=protein&id=3064594085,3064593987,3064593981,3064593977,3064593963,3064593961,3064593945,3064593925,3064593923,3064593913,3064593909,3064593905,3064593903,3064593901,3355890172,3355890152,3355890132,3355890112,3355890092,3355890072,3355890052,3355890032,3355890012,3355889992&rettype=fasta&retmode=text

`public_HA.fasta` SHA-256: `f63ecf106b745bbcaf371c1d3bf2a3062e3dd5ee6c9884535b535bcc80087689`.
The FASTA headers preserve all 24 accession/version identifiers. All records have 566 amino-acid positions. One has an ambiguous residue in the analyzed window.

This is a fixed software-integration fixture, not a representative surveillance panel. The free-text year query does not establish collection dates. No biological performance claims are inferred from this selection.

`public_HA_expected.json` contains an independent expected substitution-count oracle: compare raw input positions 84–284 directly with the fixed `YAO02406.1` reference, excluding noncanonical amino acids. It does not call FluTrees mutation or alignment functions. The integration test requires real MAFFT, checks these counts, and verifies partition conservation.
