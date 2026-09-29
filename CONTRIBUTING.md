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

Update the version in `pyproject.toml`, `src/flutrees/__init__.py`, `CITATION.cff`, the CLI version test, and the installation guide. Update `CHANGELOG.md`, `docs/RELEASE_NOTES.md`, and the citation release date. CI checks version consistency and builds the release downloads on each branch.

Run the full CI suite on the proposed commit before moving it to main. After all tests and packaging checks pass on main, CI publishes a new version as a GitHub release with a wheel, source archive, test kit, example PDF, and checksums. Existing releases are left unchanged. Only the publication job has repository write permission.
