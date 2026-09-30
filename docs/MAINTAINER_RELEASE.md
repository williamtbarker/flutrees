# FluTrees 0.3.2: maintainer testing and publication

Run the local checks in a separate checkout and environment. Keep the working 0.3.1 installation available until acceptance is complete. Run each block in order and stop on an unexpected failure. The GUI checks require an actual desktop session.

The release sequence is **local acceptance → branch push → pull-request CI → merge → main CI → automatic publication**. A branch push alone does not publish. Merging to main authorizes publication after every release gate passes. Do not create the `v0.3.2` tag manually: the workflow creates the tag and release together.

## 1. Obtain the candidate

If supplied as `flutrees-0.3.2-candidate.bundle`, save it in Downloads and run:

```bash
git clone --branch release/v0.3.2 \
  "$HOME/Downloads/flutrees-0.3.2-candidate.bundle" \
  "$HOME/Desktop/flutrees-0.3.2-test"
cd "$HOME/Desktop/flutrees-0.3.2-test"
git remote set-url origin https://github.com/williamtbarker/flutrees.git
git fetch origin --tags
git status --short
git log -1 --oneline
```

The destination must be a new directory. `git status --short` should print nothing. A bundle contains Git history and the candidate branch; it is not the final customer Test Kit.

If the candidate branch is already on GitHub, use a fresh clone instead:

```bash
git clone --branch release/v0.3.2 \
  https://github.com/williamtbarker/flutrees.git \
  "$HOME/Desktop/flutrees-0.3.2-test"
cd "$HOME/Desktop/flutrees-0.3.2-test"
```

## 2. Set up macOS testing

These instructions assume Homebrew is installed. Leave any active conda environment before activating the new venv. First check the prerequisites you already have:

```bash
python3.13 --version
python3.13 -m tkinter
mafft --version
```

Close the small Tk demonstration window. If all three checks work, skip system installation. If a check fails because a component is missing, install only that component:

| Missing component | Homebrew command |
|---|---|
| Python 3.13 | `brew install python@3.13` |
| Tk for that Homebrew Python | `brew install python-tk@3.13` |
| MAFFT | `brew install mafft` |

Homebrew can upgrade existing packages and compile dependencies when asked to install them again. Do not reinstall working prerequisites just to test this release. Graphviz and GitHub CLI are checked separately where needed below; neither is required to launch FluTrees or generate its normal PDF, SVG, and PNG figures. Use the same Python executable throughout environment creation and activation.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --only-binary=:all: -e '.[dev]'
python -m tkinter
```

Close the small Tk demonstration window, then verify the tools:

```bash
python --version
mafft --version
flutrees --version
flutrees --help
```

Expect FluTrees **0.3.2**, a working MAFFT executable, and help containing all five layout options. Use MAFFT 7.487 or later; retain the exact version in your acceptance notes. The setup is based on the [Homebrew Tk formula](https://formulae.brew.sh/formula/python-tk@3.13). The pip command requires prebuilt distributions for downloaded dependencies; if one is unavailable for your platform, investigate that package before allowing a source build.

For Ubuntu/Debian, install `mafft graphviz python3-venv python3-tk xvfb xauth`, create a venv with `python3`, and install the same Python dependencies. In section 4, use `python -m playwright install --with-deps chromium` for the browser download. Prefix the full pytest command below with `xvfb-run -a`. macOS uses its native desktop without Xvfb or an artificial `DISPLAY` value.

## 3. Automated application checks

The full suite includes native Graphviz rendering. Check `dot -V` first and retain a working installation. If it is missing, install Graphviz (`brew install graphviz` on macOS) before running the suite. A source build can pull in many dependencies. You can use the [GUI quickstart](../README.md#quickstart-gui-mode) while resolving this optional renderer, but a skipped Graphviz test does not count as complete maintainer acceptance.

From the checkout root, with `.venv` active:

```bash
mkdir -p validation
git worktree add --detach validation/legacy 5683105e015e19ccaa5744789de9ad8941331975
python -m ruff check .
python -m mypy src/flutrees --ignore-missing-imports --check-untyped-defs
python -m mypy src/flutrees/config.py src/flutrees/layout.py \
  --strict --follow-imports=silent --ignore-missing-imports
python -m pytest --cov=flutrees --cov-branch \
  --cov-report=term-missing --cov-report=json --cov-report=xml \
  --cov-fail-under=100 --junitxml=validation/local-tests.xml
python - <<'PY'
import json
import xml.etree.ElementTree as ET
coverage = json.load(open('coverage.json'))['totals']
assert coverage['missing_lines'] == coverage['missing_branches'] == coverage['excluded_lines'] == 0, coverage
suites = ET.parse('validation/local-tests.xml').getroot().findall('testsuite')
assert suites and sum(int(s.get('tests', '0')) for s in suites) == 261
for suite in suites:
    assert all(int(suite.get(k, '0')) == 0 for k in ('failures', 'errors', 'skipped')), suite.attrib
print('PASS: 261 tests; no failures, errors, skips, or coverage gaps.')
PY
```

Create the legacy worktree once; on subsequent runs retain it. The suite verifies its historical files against stored hashes. It includes 5,000 generated scientific cases and a physical Excel row-limit test, so let it finish. Desktop windows may briefly appear during the native checks. All 261 tests should pass, including both native GUI cases; a skip is not full local acceptance.

## 4. CLI, data, and report checks

This section also checks browser rendering and the Graphviz installation verified above. Install the browser test dependency and its browser:

```bash
python -m pip install --only-binary=:all: playwright
python -m playwright install chromium
```

Use the following run names once. If repeating this section, choose new names and update the comparison paths rather than deleting previous results.

```bash
flutrees --demo --tree-mode frequency --legacy-alignment --threads 1 \
  --outdir validation/manual --run-id cli_default
flutrees --demo --tree-mode all --reproducible --threads 1 \
  --outdir validation/manual --run-id cli_all
flutrees --demo --tree-mode all --reproducible --threads 1 \
  --figure-width 9 --figure-height 12 --level-spacing 2 --node-spacing 3 --line-width 2.5 \
  --outdir validation/manual --run-id cli_styled
flutrees --demo --max-depth 0 --threads 1 \
  --outdir validation/manual --run-id cli_root
flutrees -i tests/data/public_HA.fasta --tree-mode all --threads 1 \
  --outdir validation/manual --run-id cli_public
python tests/browser_check.py validation/manual/cli_all/example/START_HERE.html
```

Check that restyling leaves the scientific results unchanged:

```bash
python - <<'PY'
import json
from pathlib import Path
from pypdf import PdfReader
base = Path('validation/manual')
a, b = base / 'cli_all/example', base / 'cli_styled/example'
assert json.loads((a / 'provenance.json').read_text())['analysis_id'] == json.loads((b / 'provenance.json').read_text())['analysis_id']
for mode in ('frequency', 'balanced', 'diversity'):
    for name in ('tree_full.json', 'tree_pruned.json', 'group_assignments.tsv'):
        relative = Path('trees') / mode / name
        assert (a / relative).read_bytes() == (b / relative).read_bytes(), relative
    page = PdfReader(b / 'trees' / mode / 'tree_full.pdf').pages[0]
    assert float(page.mediabox.width) == 648 and float(page.mediabox.height) == 864
root = json.loads((base / 'cli_root/example/tree_full.json').read_text())
assert root['left'] is None and root['right'] is None
for name in ('cli_default', 'cli_all', 'cli_styled', 'cli_root', 'cli_public'):
    assert json.loads((base / name / 'status.json').read_text())['status'] == 'complete'
print('PASS: presentation invariance, portrait dimensions, root-only tree, and completed runs.')
PY
```

In Finder, open `validation/manual/cli_all/START_HERE.html`. Inspect its linked dataset overview, PDFs, workbook, text trace, and each named tree mode. Browser expand/collapse, membership tables, and image links should work offline. The synthetic example has 48 records, mutation counts 12/12/24, and four terminal groups of 12; the public HA input has 24 records. Default frequency workbooks have seven sheets; all-mode workbooks also contain the cross-view sheets. Check workbook Parameters against the command you ran.

Render the optional DOT output to verify Graphviz:

```bash
dot -Tsvg validation/manual/cli_all/example/tree_full.dot \
  -o validation/manual/tree_graphviz.svg
```

## 5. Native desktop acceptance

```bash
flutrees --gui
```

Use an absolute results-folder path ending in `flutrees-0.3.2-test/validation/manual`, selected with **Browse**. The rows below are interactive checks; record failures with a screenshot and the run folder. Restore a valid field after each deliberately invalid value.

| Check | What to do | Expected result |
|---|---|---|
| Inputs | Use included example, add the same path again, remove a selected file, clear, and reload the example. | One entry per resolved file; correct paths; Analyze with no inputs gives a useful error. |
| Default run | Keep defaults, CPU threads = 1, Run ID = `gui_default`; analyze. | Complete result, 48 records, four groups of 12, working Open results and populated Tree viewer. |
| Customer settings | Run ID = `gui_custom`, Tree view = all, Max depth = 1, Min split = 2, Min freq = 0.25, Prune cutoff = 20, threads = 1, alignment = Reproducible. | Recorded values match; all full trees stop at depth 1; all three modes exist. |
| CLI equivalence | After that run, change only Run ID to `cli_from_gui` and Copy CLI command. Close the GUI, paste the command into the activated terminal, and run it. | Same tree JSON and assignments as `gui_custom`; verify with the comparison block below. |
| Window layout | Reopen the GUI; resize toward its minimum size, scroll Analysis, visit every tab. | Analyze/status actions stay visible; fields remain reachable; viewer controls fit. |
| Tree choice | Open saved run: `validation/manual/cli_all`. Select every mode and both full/pruned trees. | The selected tree displays with correct counts and labels. No alignment reruns. |
| Aspect and spacing | Width = 9, Height = 12, Level gap = 2, Node gap = 3, Line width = 2.5; Apply layout; toggle Whole page. Then try 14 × 8.5 and both gap limits, 0.25 and 4. | Whole page shows the requested aspect; node boxes remain separated and within the page; visible gaps/strokes respond to controls. |
| Zoom and pan | Zoom in several times, drag, use both scrollbars, resize, then Fit. | Navigation works; Fit restores the whole tree or page, according to Whole page. |
| Export | Save one PNG, SVG, and PDF into `validation/manual`, outside the completed run folder. Open each. | Current displayed layout exported; PDF page dimensions are correct; SVG contains editable text; tree counts remain unchanged. |
| Layout error | Enter `nan` for width and Apply layout, then correct it. | Clear error, stale preview cleared, Save disabled until a valid render succeeds. |
| Input errors | Try Min freq = `5%`, depth = 21, Min split = 0, CPU threads = 0, and Run ID = `../bad`, separately. | Each fails before analysis; no invalid run is produced. |
| Existing run | Reuse `gui_default` in the same results folder. | Refused; the previous run remains intact. |
| Worker error | Choose a new run ID and set MAFFT executable to `missing_mafft_executable`; analyze, then restore `mafft`. | Actionable failure in Run log; controls unlock and the next valid run works. |
| Saved-run error | Open an empty folder or a dataset folder instead of the enclosing completed run folder. | Useful error, no application crash. |
| Multiple inputs | Select the example and `tests/data/public_HA.fasta`, clear Reference ID, use a new run ID, and analyze. | Separate dataset folders with 48 and 24 records; no pooling. |
| Reference and window | On the example alone, use the Reference ID printed below this table, first/last residues 100/250, and a new run ID. Then try a nonexistent reference with another run ID. | First run records that exact reference and window; second gives an explicit error. |
| Lifecycle | While a run is active, try editing settings and closing. Finish, close, relaunch with `flutrees-gui`, and run again. | Settings lock; close waits for the active run; subsequent launches and analyses succeed. |
| Own data | Analyze one small, non-confidential HA protein dataset whose expected behavior you know. | Reference, numbering, mutations, groups, and reports make scientific sense for that input. |

Reference ID for the reference/window check, pasted exactly:

```text
Synthetic|Example/Group1/1/2026|DEMO001|HA|synthetic
```

After completing the CLI-equivalence row, run:

```bash
python - <<'PY'
from pathlib import Path
root = Path('validation/manual')
for mode in ('frequency', 'balanced', 'diversity'):
    for filename in ('tree_full.json', 'tree_pruned.json', 'group_assignments.tsv'):
        relative = Path('example/trees') / mode / filename
        assert (root / 'gui_custom' / relative).read_bytes() == (root / 'cli_from_gui' / relative).read_bytes(), relative
print('PASS: GUI and copied CLI scientific outputs match.')
PY
```

## 6. Check a tree with continuation pages

The bundled 48-record example is too shallow to exercise page navigation. Create a separate synthetic layout panel from the public fixture, with five independent binary substitutions. This is a software layout fixture, not a biological test panel.

```bash
python - <<'PY'
from pathlib import Path
from Bio import SeqIO
folder = Path('validation/manual-inputs')
folder.mkdir(parents=True, exist_ok=True)
base = str(next(SeqIO.parse('tests/data/public_HA.fasta', 'fasta')).seq)
with (folder / 'layout_panel.fasta').open('x') as out:
    for i in range(32):
        seq = list(base)
        for bit, position in enumerate((100, 125, 150, 175, 200)):
            if i & (1 << bit):
                seq[position - 1] = 'A' if base[position - 1] != 'A' else 'V'
        out.write(f'>layout_{i:02d}\n' + ''.join(seq) + '\n')
PY
flutrees -i validation/manual-inputs/layout_panel.fasta \
  --tree-mode frequency --reproducible --threads 1 --reference-id layout_00 \
  --max-depth 10 --min-split 1 --min-freq 0 --prune-cutoff 1 \
  --outdir validation/manual --run-id layout_panel
```

In Tree viewer, open `validation/manual/layout_panel`. Expect 63 nodes across a depth-5 tree and nine full-tree PDF/viewer pages for this fixture. Move through all pages and back. Every continuation label should point to its stated page. Zoom must reset on page changes; no page should omit or clip its visible nodes. Open `cli_root` afterward to verify that a single root also gets a useful fitted view. These expected counts were checked with MAFFT 7.505; investigate differences with another aligner version.

## 7. Build and test the actual wheel

```bash
python -m build
python -m venv validation/wheel-env
validation/wheel-env/bin/python -m pip install dist/flutrees-0.3.2-py3-none-any.whl
mkdir -p validation/wheel-smoke
(
  cd validation/wheel-smoke
  ../wheel-env/bin/python -c 'import flutrees; print(flutrees.__file__); assert "site-packages" in flutrees.__file__'
  ../wheel-env/bin/flutrees --version
  ../wheel-env/bin/flutrees --demo --tree-mode all --threads 1 \
    --outdir runs --run-id wheel_example
)
```

The import path must point inside `validation/wheel-env`, and the installed wheel must complete all three tree views. This tests installation from a built artifact outside the source directory. Release CI separately executes the README's venv, conda, and uv installers and the six performance workloads through 25,000 records; those Linux jobs remain required even after local acceptance.

## 8. Push the branch and run GitHub acceptance

Proceed only after the local manual checks and automated checks pass. Check for GitHub CLI with `gh --version`. If it is missing, install it (`brew install gh` on macOS); retain an existing working installation. From the repository root:

```bash
gh auth status
```

If GitHub CLI is not signed in, authenticate through its browser flow:

```bash
gh auth login --hostname github.com --git-protocol https --web --scopes repo,workflow
gh auth setup-git
```

Review the exact proposed changes. `git status --short` must be empty; validation outputs are ignored and must stay out of the commit. Check release notes, version metadata, intended source/tests/docs, and the commit author/message. If origin/main changed since local testing, reconcile the changes on the branch and retest before continuing.

```bash
git fetch origin --tags
git status --short
git diff --check origin/main...HEAD
git diff --stat origin/main...HEAD
git log --format=fuller origin/main..HEAD
git push -u origin release/v0.3.2
gh pr create --repo williamtbarker/flutrees --base main --head release/v0.3.2 \
  --title 'Release FluTrees 0.3.2' --body-file docs/RELEASE_NOTES.md
gh pr checks release/v0.3.2 --repo williamtbarker/flutrees --watch
```

Wait for the checks to register if GitHub initially reports none. Require all four Python jobs, browser, all three installers, all six performance sizes, alignment, and package to succeed. The publication job is intentionally skipped on a pull request. Read failed logs and fix the branch rather than bypassing a failed gate. The [GitHub CLI checks command](https://cli.github.com/manual/gh_pr_checks) supports watching the complete check set; do not limit it to repository-required checks if some release jobs are not marked required.

## 9. Merge and let CI publish

After local acceptance and successful PR checks, this is the publication decision:

```bash
gh pr checks release/v0.3.2 --repo williamtbarker/flutrees
gh pr merge release/v0.3.2 --repo williamtbarker/flutrees \
  --squash --match-head-commit "$(git rev-parse HEAD)" \
  --subject 'Release FluTrees 0.3.2' --body-file docs/RELEASE_NOTES.md
gh run list --repo williamtbarker/flutrees --workflow ci.yml --branch main --event push --limit 5
gh run watch --repo williamtbarker/flutrees --exit-status
```

For `gh run watch`, select the main-branch run created by this merge. Refresh the list if the run has not appeared yet. The [merge command](https://cli.github.com/manual/gh_pr_merge) checks that the PR head still matches the commit you tested. Main repeats the release gates, packages their actual evidence, and creates **v0.3.2** only after success. It leaves older releases unchanged. Do not push a tag or manually upload an unvalidated local Test Kit alongside this workflow.

## 10. Verify the published download

After the main workflow succeeds:

```bash
gh release view v0.3.2 --repo williamtbarker/flutrees --web
gh release download v0.3.2 --repo williamtbarker/flutrees --dir validation/release-download
(
  cd validation/release-download
  shasum -a 256 -c SHA256SUMS.txt
  unzip FluTrees_v0.3.2_Test_Kit.zip
  cd FluTrees_v0.3.2_Test_Kit
  shasum -a 256 -c SHA256SUMS.txt
  open START_HERE.html
)
```

The release must contain the wheel, source archive, Test Kit, example PDF, and checksums. Inspect `BUILD_INFO.txt` in the kit: it must identify the successful main commit and CI run. Open both included example reports, PDF and workbook links, and the installation guide. The [download command](https://cli.github.com/manual/gh_release_download) targets the explicit version so a later release cannot change this check.

On Linux, replace `shasum -a 256 -c` with `sha256sum -c` and `open` with `xdg-open`. If a check or publication step fails, preserve its logs and stop; an existing published version should not be deleted or replaced to force a release through.
