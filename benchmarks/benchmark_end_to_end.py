"""Measure the installed CLI from full-length HA FASTA through every export.

The public fixture is repeated without altering residues. This tests software
scale and retains its original allele spectrum; it is not a surveillance sample.
"""

import argparse
import csv
import hashlib
import json
import os
import platform
import pstats
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from Bio import SeqIO

from flutrees import __version__


NAMESPACE = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RELATIONSHIPS = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare_input(source, destination, records):
    panel = list(SeqIO.parse(source, "fasta"))
    if not panel or records < 1:
        raise ValueError("The source fixture and requested record count must be nonempty.")
    with destination.open("w", encoding="utf-8") as stream:
        for i in range(records):
            record = panel[i % len(panel)]
            stream.write(f">panel_{i:08d} source={record.id}\n{record.seq}\n")
    return {"source_sha256": sha256(source), "source_records": len(panel),
            "sequence_lengths": sorted({len(r.seq) for r in panel}),
            "input_sha256": sha256(destination), "input_records": records,
            "design": "Repeat public HA fixture without residue edits; assign unique transport-independent IDs."}


def worksheet_rows(workbook):
    """Count actual worksheet rows incrementally, including continuation sheets."""
    counts = {}
    with zipfile.ZipFile(workbook) as archive:
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        paths = {r.attrib["Id"]: r.attrib["Target"] for r in relationships}
        book = ET.fromstring(archive.read("xl/workbook.xml"))
        for sheet in book.find(NAMESPACE + "sheets"):
            relation = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            target = paths[relation]
            target = target.lstrip("/") if target.startswith("/") else "xl/" + target
            count = 0
            with archive.open(target) as stream:
                for _, element in ET.iterparse(stream, events=("end",)):
                    if element.tag == NAMESPACE + "row":
                        if element.find(NAMESPACE + "c") is not None:
                            count += 1
                        element.clear()
            counts[sheet.attrib["name"]] = max(0, count - 1)
    return counts


def verify_results(out, records):
    """Check every published artifact and independently conserve all memberships."""
    status = json.loads((out / "status.json").read_text())
    if status["status"] != "complete":
        raise ValueError("Benchmark analysis did not complete.")
    for name, size in status["artifacts"].items():
        if not (out / name).is_file() or (out / name).stat().st_size != size or not size:
            raise ValueError(f"Invalid published artifact: {name}")
    expected_ids = {f"panel_{i:08d}" for i in range(records)}
    all_members = 0
    mode_metrics = {}
    for mode in ("frequency", "balanced", "diversity"):
        membership = 0
        groups = {}
        node_count = 0
        for view in ("full", "pruned"):
            tree = json.loads((out / "trees" / mode / f"tree_{view}.json").read_text())
            if set(tree["record_ids"]) != expected_ids:
                raise ValueError(f"Missing root records in {mode}/{view}")
            stack = [tree]
            ids = set()
            while stack:
                node = stack.pop()
                node_count += 1
                members = set(node["record_ids"])
                if len(members) != node["support"] or node["node_id"] in ids:
                    raise ValueError("Invalid node support or identity.")
                ids.add(node["node_id"])
                membership += len(members)
                children = [c for c in (node["left"], node["right"]) if c is not None]
                covered = set()
                for child in children:
                    child_members = set(child["record_ids"])
                    if not child_members < members or covered & child_members:
                        raise ValueError("Child partition is invalid.")
                    covered.update(child_members)
                    stack.append(child)
                if view == "full":
                    if children and (len(children) != 2 or covered != members):
                        raise ValueError("Full-tree partition loses records.")
                    if not children:
                        for record in members:
                            if record in groups:
                                raise ValueError("Duplicate terminal assignment.")
                            groups[record] = node["node_id"]
            if view == "full" and set(groups) != expected_ids:
                raise ValueError("Full-tree leaves do not cover the input.")
        with (out / "trees" / mode / "group_assignments.tsv").open(newline="") as stream:
            assignments = list(csv.DictReader(stream, delimiter="\t"))
        if len(assignments) != records or {r["record_id"] for r in assignments} != expected_ids:
            raise ValueError("Assignment export loses or duplicates records.")
        if any(groups[r["record_id"]] != int(r["full_group_id"]) for r in assignments):
            raise ValueError("Assignment export disagrees with tree leaves.")
        mode_metrics[mode] = {"full_and_pruned_nodes": node_count, "membership_rows": membership,
                              "terminal_groups": len(set(groups.values()))}
        all_members += membership
    rows = worksheet_rows(out / "results.xlsx")
    totals = {}
    for name, count in rows.items():
        logical = re.sub(r" \(\d+\)$", "", name)
        totals[logical] = totals.get(logical, 0) + count
    for name, expected in {"Records": records, "Tree Groups": records * 3,
                           "All Membership": all_members,
                           "Node Membership": mode_metrics["frequency"]["membership_rows"]}.items():
        if totals.get(name) != expected:
            raise ValueError(f"Workbook {name}: expected {expected}, found {totals.get(name)}")
    return {"modes": mode_metrics, "workbook_sheet_rows": rows,
            "artifact_count": len(status["artifacts"]),
            "artifact_bytes": sum(status["artifacts"].values()),
            "record_conservation": "passed", "workbook_conservation": "passed"}


def run_case(source, records, root, threads):
    root.mkdir(parents=True, exist_ok=False)
    fasta = root / "panel.fasta"
    fixture = prepare_input(source, fasta, records)
    profile = root / "pipeline.prof"
    command = [sys.executable, "-m", "cProfile", "-o", str(profile), "-m", "flutrees",
               "-i", str(fasta), "-o", str(root / "results"), "--run-id", "benchmark",
               "--tree-mode", "all", "--threads", str(threads)]
    resource_log = root / "resources.json"
    timed_command = ["/usr/bin/time", "-o", str(resource_log), "-f",
                     '{"max_rss_kib":%M,"wall_seconds":%e,"user_seconds":%U,"system_seconds":%S}', *command]
    started = time.perf_counter()
    with (root / "cli.log").open("w") as log:
        result = subprocess.run(timed_command, stdout=log, stderr=subprocess.STDOUT, check=False, timeout=1800)
    seconds = time.perf_counter() - started
    if result.returncode:
        raise RuntimeError(f"CLI failed with exit {result.returncode}. See {root / 'cli.log'}")
    out = root / "results/benchmark/panel"
    verified = verify_results(out, records)
    functions = {}
    wanted = {"mafft_align", "load_fasta_extract_all", "call_mutations", "build_tree", "write_workbook",
              "write_html", "write_pdf", "write_tree_figures", "comparison_tables"}
    for (filename, _, function), stats in pstats.Stats(str(profile)).stats.items():
        if function in wanted and "flutrees" in filename:
            functions[function] = {"calls": stats[1], "cumulative_seconds": round(stats[3], 6)}
    if functions.get("mafft_align", {}).get("calls") != 1 or functions.get("build_tree", {}).get("calls") != 3:
        raise ValueError("Expected one alignment and three tree constructions.")
    provenance = json.loads((out / "provenance.json").read_text())
    measurement = {
        "schema_version": 1, "version": __version__, "source_commit": os.environ.get("GITHUB_SHA", "local"),
        "records": records, "threads": threads, "total_cli_seconds": round(seconds, 6),
        "resources": json.loads(resource_log.read_text()),
        "resource_note": "GNU time maximum resident set size; not a sum of simultaneously resident processes.",
        "command": command, "fixture": fixture, "functions": functions, "verification": verified,
        "versions": provenance["versions"], "platform": platform.platform(),
        "cpu_count": os.cpu_count(), "alignment_sha256": provenance["alignment_sha256"],
        "measurement_note": "Real installed CLI with cProfile enabled, including validation, MAFFT and all exports. Function timings are cumulative and may overlap; verification runs afterward.",
    }
    (root / "measurement.json").write_text(json.dumps(measurement, indent=2) + "\n")
    print(json.dumps({"records": records, "seconds": seconds, "verification": "passed"}), flush=True)
    return measurement


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("tests/data/public_HA.fasta"))
    parser.add_argument("--sizes", nargs="+", type=int, default=[100, 500, 1000, 5000, 10000, 25000])
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    if any(n < 1 for n in args.sizes) or args.threads < 1:
        parser.error("Record counts and threads must be positive.")
    args.outdir.mkdir(parents=True, exist_ok=True)
    measurements = [run_case(args.input.resolve(), n, args.outdir.resolve() / str(n), args.threads) for n in args.sizes]
    (args.outdir / "end-to-end.json").write_text(json.dumps(measurements, indent=2) + "\n")


if __name__ == "__main__":
    main()
