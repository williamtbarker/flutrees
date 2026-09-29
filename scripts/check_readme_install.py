"""Execute documented installation commands in an isolated home directory."""

import argparse
import hashlib
import json
import os
import platform
import re
import runpy
import subprocess
import tempfile
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("venv", "conda", "uv"), required=True)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    readme = (repository / "README.md").read_text(encoding="utf-8")
    pattern = rf"<!-- install-check: {args.mode} -->\s*```bash\n(.*?)```"
    matches = re.findall(pattern, readme, flags=re.DOTALL)
    if len(matches) != 1:
        raise ValueError("Expected exactly one named README installation block.")
    code = matches[0]
    version = runpy.run_path(str(repository / "src/flutrees/__init__.py"))["__version__"]
    args.output.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f"flutrees-{args.mode}-"))
    home = work / "home"
    home.mkdir()
    commands = work / "readme.sh"
    commands.write_text(code, encoding="utf-8")
    env = os.environ.copy()
    for name in list(env):
        if name.startswith(("CONDA_", "UV_", "PYTHONPATH", "VIRTUAL_ENV")):
            env.pop(name)
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"),
               FLUTREES_PACKAGE=str(args.wheel.resolve()), FLUTREES_REF=args.ref,
               PIP_DISABLE_PIP_VERSION_CHECK="1")
    log = args.output / f"{args.mode}.log"
    started = time.perf_counter()
    with log.open("w") as stream:
        result = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", str(commands)],
                                cwd=work, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=1200, check=False)
    if result.returncode:
        raise RuntimeError(f"README {args.mode} commands failed: exit {result.returncode}; {log}")
    if args.mode == "venv":
        root = work / "flutrees/results"
    elif args.mode == "uv":
        root = home / "flutrees-work/results"
        if not (home / ".local/bin/uv").is_file():
            raise ValueError("The standalone uv bootstrap did not install its executable.")
    else:
        root = work / "results"
        if not (home / "miniconda3/bin/conda").is_file():
            raise ValueError("The downloaded Miniconda bootstrap did not install conda.")
    summaries = list(root.rglob("summary.json"))
    if len(summaries) != (2 if args.mode == "venv" else 1):
        raise ValueError("README examples did not produce the expected datasets.")
    datasets = []
    for path in summaries:
        summary = json.loads(path.read_text())
        status = json.loads(path.with_name("status.json").read_text())
        if summary["version"] != version or summary["tree_modes"] != ["frequency", "balanced", "diversity"]:
            raise ValueError("Installed package or generated tree modes do not match the candidate.")
        if status["status"] != "complete":
            raise ValueError("README example did not complete.")
        for name, size in status["artifacts"].items():
            if not (path.parent / name).is_file() or (path.parent / name).stat().st_size != size:
                raise ValueError(f"Invalid README example artifact: {name}")
        datasets.append({"input": summary["input_name"], "records": summary["n_records"],
                         "modes": summary["tree_modes"], "artifacts": len(status["artifacts"])})
    record = {"mode": args.mode, "version": version, "ref": args.ref, "platform": platform.platform(),
              "readme_block_sha256": hashlib.sha256(code.encode()).hexdigest(),
              "wheel_sha256": hashlib.sha256(args.wheel.read_bytes()).hexdigest(),
              "seconds": round(time.perf_counter() - started, 3), "datasets": datasets,
              "status": "passed", "commands_modified": False,
              "overrides": {"FLUTREES_REF": args.ref, "FLUTREES_PACKAGE": args.wheel.name},
              "scope": "Verbatim Linux README commands, including standalone installer download and execution where applicable; isolated HOME and environment."}
    (args.output / f"{args.mode}.json").write_text(json.dumps(record, indent=2) + "\n")
    (args.output / f"{args.mode}-commands.sh").write_text(code)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
