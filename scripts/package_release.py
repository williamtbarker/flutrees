"""Build checked release assets only from completed validation jobs."""

import hashlib
import html
import json
import os
import re
import runpy
import shutil
import tomllib
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

root = Path.cwd()
version = tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]
assert re.fullmatch(r"\d+\.\d+\.\d+", version), version
assert runpy.run_path("src/flutrees/__init__.py")["__version__"] == version
assert f"version: {version}\n" in Path("CITATION.cff").read_text()
assert Path("docs/RELEASE_NOTES.md").read_text().startswith(f"# FluTrees {version}\n")
assert f"## {version} " in Path("CHANGELOG.md").read_text()
wheel_name = f"flutrees-{version}-py3-none-any.whl"
assert wheel_name in Path("docs/TESTING_GUIDE.md").read_text()
totals = json.loads(Path("validation/coverage.json").read_text())["totals"]
assert totals["missing_lines"] == totals["missing_branches"] == 0, totals

kit = root / "build" / f"FluTrees_v{version}_Test_Kit"
output = root / "build" / "release"
(kit / "package").mkdir(parents=True)
(kit / "example_inputs").mkdir()
(kit / "validation").mkdir()
output.mkdir()
wheel = Path("validation/dist") / wheel_name
sdist = Path("validation/dist") / f"flutrees-{version}.tar.gz"
for file in (wheel, sdist):
    assert file.is_file() and file.stat().st_size > 0, file
    shutil.copy2(file, output / file.name)
with zipfile.ZipFile(wheel) as archive:
    for source in Path("src/flutrees").rglob("*.py"):
        assert archive.read(source.relative_to("src").as_posix()) == source.read_bytes(), source
shutil.copy2(wheel, kit / "package" / wheel.name)
shutil.copytree("validation/examples", kit / "examples")
for source in ("src/flutrees/data/example.fasta", "tests/data/public_HA.fasta", "tests/data/public_HA_expected.json"):
    shutil.copy2(source, kit / "example_inputs" / Path(source).name)
shutil.copy2("tests/data/README.md", kit / "example_inputs/PUBLIC_DATA_PROVENANCE.md")
for source in ("README.md", "CHANGELOG.md", "LICENSE", "CITATION.cff", "docs/TESTING_GUIDE.md", "docs/RELEASE_NOTES.md"):
    shutil.copy2(source, kit / Path(source).name)
(kit / "docs").mkdir()
for source in Path("docs").iterdir():
    if source.suffix in {".md", ".json"}:
        shutil.copy2(source, kit / "docs" / source.name)
shutil.copy2("validation/coverage.json", kit / "validation/coverage-python311.json")
shutil.copy2("validation/tests.xml", kit / "validation/tests-python311.xml")
shutil.copytree("acceptance", kit / "validation/acceptance")
performance = list(Path("acceptance").glob("performance-*/measurement.json"))
assert sorted(json.loads(p.read_text())["records"] for p in performance) == [100, 500, 1000, 5000, 10000, 25000]
for report in performance:
    result = json.loads(report.read_text())
    assert result["version"] == version
    assert result["verification"]["record_conservation"] == "passed"
    assert result["verification"]["workbook_conservation"] == "passed"
for mode in ("venv", "conda", "uv"):
    result = json.loads((Path("acceptance") / f"installer-{mode}/{mode}.json").read_text())
    assert result["status"] == "passed" and result["version"] == version
    assert result["commands_modified"] is False
alignment = json.loads(Path("acceptance/alignment/alignment-comparison.json").read_text())
assert len(alignment["runs"]) == 18 and alignment["version"] == version

shutil.copy2("docs/RELEASE_START.html", kit / "START_HERE.html")
guide = html.escape((kit / "TESTING_GUIDE.md").read_text())
(kit / "TESTING_GUIDE.html").write_text(
    '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    '<title>FluTrees installation and testing</title><style>body{font:17px system-ui;max-width:950px;margin:auto;padding:30px;line-height:1.6}'
    'pre{white-space:pre-wrap;font:inherit}</style><p><a href="START_HERE.html">Back to Start here</a></p>'
    f'<pre>{guide}</pre></html>', encoding="utf-8")
(kit / "BUILD_INFO.txt").write_text(
    f"FluTrees {version}\nSource commit: {os.environ['GITHUB_SHA']}\n"
    f"CI: https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}\n"
    "The wheel and examples come from the Python 3.11 validation job in this CI run.\n"
    "Application statement and branch coverage: 100%.\n"
    "Python, third-party Python dependencies, and MAFFT are not bundled.\n", encoding="utf-8")
for status in (kit / "examples").rglob("status.json"):
    assert json.loads(status.read_text())["status"] == "complete", status
checksums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(kit).as_posix()}\n"
                    for p in sorted(kit.rglob("*")) if p.is_file())
(kit / "SHA256SUMS.txt").write_text(checksums, encoding="utf-8")

class Links(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in {"href", "src"} and value:
                parsed = urlsplit(value)
                if not parsed.scheme and not parsed.netloc and parsed.path:
                    target = (self.folder / unquote(parsed.path)).resolve()
                    assert kit.resolve() in target.parents and target.is_file(), target

for document in kit.rglob("*.html"):
    parser = Links()
    parser.folder = document.parent
    parser.feed(document.read_text())
archive_path = output / f"{kit.name}.zip"
with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(kit.rglob("*")):
        if file.is_file():
            archive.write(file, file.relative_to(kit.parent))
with zipfile.ZipFile(archive_path) as archive:
    assert archive.testzip() is None
shutil.copy2(kit / "examples/synthetic/example/tree_full.pdf", output / f"FluTrees_v{version}_Example_Tree.pdf")
(output / "SHA256SUMS.txt").write_text("".join(
    f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in sorted(output.iterdir())), encoding="utf-8")
with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
    stream.write(f"version={version}\n")
print(f"Verified release files for FluTrees {version}:")
for file in sorted(output.iterdir()):
    print(f"  {file.name}: {file.stat().st_size} bytes")
