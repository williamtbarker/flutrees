# Contributing to flutrees

Contributions that improve correctness, reproducibility, portability, documentation, testing, or usability are welcome.

## Development workflow

1. Fork or clone the repository.
2. Create a focused branch for the change.
3. Install the project and its development dependencies.
4. Make the smallest change that addresses the problem.
5. Run the project's formatting, linting, and test suite.
6. Update documentation and tests when behavior changes.
7. Open a pull request describing the change and its validation.

## Run the complete acceptance suite

Install MAFFT, Graphviz, Tk, Xvfb, and the development dependencies. Fetch repository history before creating the immutable comparison checkout:

```bash
git fetch origin --tags
git worktree add --detach validation/legacy 5683105e015e19ccaa5744789de9ad8941331975
python -m pip install -e '.[dev]'
ruff check .
xvfb-run -a python -m pytest --cov=flutrees --cov-branch \
  --cov-report=json --cov-report=term-missing --cov-fail-under=100
```

An existing verified baseline can be selected with `FLUTREES_LEGACY_SOURCE=/path/to/v0.2.3/src`. Tests hash its files against the committed baseline manifest; they must not substitute the current implementation for the oracle. The complete suite includes 5,000 property-generated datasets, differential subprocess runs, and the actual Excel row boundary. It is intentionally more substantial than an import smoke test.

`benchmarks/benchmark_end_to_end.py` runs real HA FASTA inputs through alignment and every requested export. `benchmarks/benchmark_alignment.py` compares both alignment profiles repeatedly. `scripts/check_readme_install.py` executes the named README blocks verbatim, including the downloaded bootstrap installers, in a separate home directory. See `docs/ACCEPTANCE.md` for the release gates and evidence paths.

## Scientific and methodological changes

Changes that affect scientific interpretation, model behavior, validation methodology, assumptions, or reported results should clearly document:

- what changed;
- why the change is justified;
- how it was tested;
- whether previously reported results are affected.

Software correctness and scientific validity should be treated as related but distinct concerns.

## Scope

Please keep contributions focused. Large changes are easier to review when discussed in an issue before implementation.

## Documentation

Write documentation for anyone using the package. Describe current behavior, reproducible steps, and relevant limitations. Keep personal correspondence, development-session notes, and unfinished planning out of public documentation and code comments.

## Releases

Update the version in `pyproject.toml`, `src/flutrees/__init__.py`, `CITATION.cff`, the CLI version test, and the installation guide. Update `CHANGELOG.md`, `docs/RELEASE_NOTES.md`, and the citation release date. CI checks version consistency and builds the release downloads on pull requests and main.

Run the full CI suite on the proposed commit before moving it to main. After all tests and packaging checks pass on main, CI publishes a new version as a GitHub release with a wheel, source archive, test kit, example PDF, and checksums. Existing releases are left unchanged. Only the publication job has repository write permission.
