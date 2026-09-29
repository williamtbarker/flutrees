"""Portable path components and reproducible, content-addressed analysis records."""

import hashlib
import json
import platform
import re
import subprocess
import unicodedata
from dataclasses import asdict
from importlib.metadata import version

from . import __version__
from .align_mafft import alignment_command, check_mafft
from .strategies import STRATEGY_VERSION


def portable_name(name):
    """Keep ordinary names stable; normalize unsafe filesystem components."""
    name = unicodedata.normalize("NFC", name).replace(" ", "_")
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f]', "_", name).rstrip(". ")
    if not name or name in {".", ".."}:
        raise ValueError("Input filename must have a usable name before its extension.")
    if re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\..*)?", name):
        name = "_" + name
    if len(name.encode("utf-8")) > 120:
        suffix = hashlib.sha256(name.encode("utf-8")).hexdigest()[:12]
        name = name.encode("utf-8")[:100].decode("utf-8", errors="ignore") + "_" + suffix
    return name


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def mafft_version(executable):
    try:
        result = subprocess.run([executable, "--version"], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, check=False, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    text = result.stdout.strip()
    return text[:1000] if result.returncode == 0 and text else "unavailable"


def analysis_provenance(cfg, out, input_sha256, reference_id, mutations):
    executable = check_mafft(cfg.mafft)
    versions = {package: version(package) for package in ("biopython", "pandas", "matplotlib", "typer", "xlsxwriter")}
    versions.update(python=platform.python_version(), flutrees=__version__, mafft=mafft_version(executable))
    mutation_bytes = json.dumps(mutations.to_dict(orient="records"), ensure_ascii=False,
                                sort_keys=True, separators=(",", ":")).encode("utf-8")
    analytical_config = asdict(cfg)
    analytical_config.pop("mafft")  # installation path is not an analytical setting
    analytical_config["threads"] = cfg.resolved_threads()
    analytical_config["reproducible"] = cfg.resolved_reproducible()
    identity = {
        "schema_version": 1, "input_sha256": input_sha256,
        "alignment_sha256": sha256_file(out / "aligned.fasta"),
        "mutation_observations_sha256": hashlib.sha256(mutation_bytes).hexdigest(),
        "reference_id": reference_id, "config": analytical_config,
        "versions": versions, "strategy_version": STRATEGY_VERSION,
    }
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        **identity, "analysis_id": hashlib.sha256(encoded).hexdigest(),
        "mafft_executable": executable,
        "mafft_command": alignment_command(executable, out / "mafft_input.fasta", cfg.resolved_threads(), cfg.resolved_reproducible()),
        "platform": platform.platform(),
        "identity_note": "Content and settings fingerprint, not a claim of cross-version or cross-platform equivalence.",
    }
