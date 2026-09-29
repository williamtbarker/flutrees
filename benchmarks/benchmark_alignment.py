"""Compare legacy and reproducible MAFFT flags on the same HA observations."""

import argparse
import hashlib
import json
import platform
import statistics
import time
from pathlib import Path

from Bio import SeqIO
from Bio.SeqRecord import SeqRecord

from flutrees import __version__
from flutrees.align_mafft import alignment_command, check_mafft, mafft_align
from flutrees.io_fasta import load_fasta_extract_all
from flutrees.mutations import call_mutations, choose_mode_reference
from flutrees.provenance import mafft_version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("tests/data/public_HA.fasta"))
    parser.add_argument("--sizes", nargs="+", type=int, default=[24, 100, 500])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    if min([args.repeats, args.threads, *args.sizes]) < 1:
        parser.error("Counts must be positive.")
    args.outdir.mkdir(parents=True, exist_ok=False)
    source = load_fasta_extract_all(args.input, 84, 284)["extracted_records"]
    executable = check_mafft("mafft")
    rows = []
    comparisons = []
    for n in args.sizes:
        input_path = args.outdir / f"input_{n}.fasta"
        SeqIO.write((SeqRecord(source[i % len(source)].seq, id=f"r{i:08d}", description="") for i in range(n)), input_path, "fasta")
        for repeat in range(args.repeats):
            # Alternate execution order to reduce systematic first-run bias.
            for reproducible in ((True, False) if repeat % 2 == 0 else (False, True)):
                mode = "reproducible" if reproducible else "legacy"
                folder = args.outdir / f"{n}-{mode}-{repeat}"
                folder.mkdir()
                aligned = folder / "aligned.fasta"
                started = time.perf_counter()
                mafft_align(input_path, aligned, executable, args.threads, reproducible)
                seconds = time.perf_counter() - started
                reference_id, reference = choose_mode_reference(aligned)
                calls = call_mutations(aligned, reference, 84)
                observations = json.dumps(calls.to_dict(orient="records"), sort_keys=True, separators=(",", ":")).encode()
                row = {"records": n, "repeat": repeat + 1, "mode": mode, "seconds": round(seconds, 6),
                       "alignment_sha256": hashlib.sha256(aligned.read_bytes()).hexdigest(),
                       "observations_sha256": hashlib.sha256(observations).hexdigest(),
                       "reference_id": reference_id,
                       "command": alignment_command(executable, input_path, args.threads, reproducible)}
                rows.append(row)
        current = [r for r in rows if r["records"] == n]
        medians = {mode: statistics.median(r["seconds"] for r in current if r["mode"] == mode)
                   for mode in ("legacy", "reproducible")}
        hashes = {mode: sorted({r["alignment_sha256"] for r in current if r["mode"] == mode})
                  for mode in ("legacy", "reproducible")}
        if len(hashes["reproducible"]) != 1:
            raise ValueError("Repeated reproducible alignments differed on the benchmark fixture.")
        comparisons.append({"records": n, "median_seconds": medians,
                            "reproducible_to_legacy_ratio": medians["reproducible"] / medians["legacy"],
                            "unique_alignment_hashes": hashes,
                            "identical_observations_across_runs_and_settings": len({r["observations_sha256"] for r in current}) == 1})
    result = {"version": __version__, "python": platform.python_version(), "platform": platform.platform(),
              "mafft_version": mafft_version(executable), "threads": args.threads,
              "fixture_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
              "window": [84, 284], "repeats_per_setting": args.repeats,
              "scope": "Repeated unmodified public-HA observations. Measures alignment only; not all possible HA diversity or hardware.",
              "comparisons": comparisons, "runs": rows}
    (args.outdir / "alignment-comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(comparisons, indent=2))


if __name__ == "__main__":
    main()
