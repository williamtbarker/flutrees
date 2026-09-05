# FluTrees

Python source for the FluTrees project.

## Scientific Purpose

FluTrees was developed to organize influenza HA sequence batches into interpretable mutation-based tree representations. The workflow includes sequence-window extraction, MAFFT alignment, reference-sequence selection, mutation calling, full and pruned tree construction, and generation of analysis artifacts for downstream review.

This repository preserves and consolidates the strongest Python implementation from the project's historical development record. Scientific assumptions and interpretation of outputs remain the responsibility of the endpoint subject-matter expert.

## Intended Use

FluTrees is intended as a research and analytical software tool for influenza hemagglutinin (HA) sequence-analysis workflows targeting the 200 amino acid antigenic region as the default for building the resulting trees. FluTrees offers flexibility at the command line to customize the HA frame of analysis. It was initially developed as a custom tool for a specific user and workflow, and public release should not be interpreted as validation for every dataset, scientific question, or operational environment.

Users should independently validate inputs, parameters, software dependencies, outputs, and scientific interpretation for their own use case. FluTrees is not presented as a clinical diagnostic device or as a substitute for expert review.

## Installation

```bash
python -m pip install -e .
```

For development:

```bash
python -m pip install -e '.[dev]'
pytest
```

The command-line entry point is:

```bash
flutrees --help
```

MAFFT must be available on `PATH` or supplied with `--mafft`.

## Repository layout

- `src/flutrees/` — canonical recovered package
- `tests/` — software-level regression tests

## If you do not have MAFFT

FluTrees requires [MAFFT](https://mafft.cbrc.jp/alignment/software/) for sequence alignment.

If MAFFT is not already installed, this repository includes a best-effort installation helper:

```bash
bash install_mafft.sh
```

The helper detects the operating system and package managers already available on the machine and attempts an appropriate MAFFT installation method. Supported paths include Homebrew, common Linux package managers, and Conda-compatible environments.

To see what the helper would attempt without making any changes:

```bash
bash install_mafft.sh --dry-run
```

To allow it to proceed without interactive confirmation:

```bash
bash install_mafft.sh --yes
```

The script does not install Homebrew, Conda, or another package manager itself. If no supported package manager is available, install MAFFT manually and verify that it is accessible with:

```bash
mafft --version
```

Common manual installation methods include:

**macOS with Homebrew**

```bash
brew install mafft
```

**Ubuntu/Debian**

```bash
sudo apt-get update
sudo apt-get install mafft
```

**Conda-compatible environment**

```bash
conda install -c conda-forge -c bioconda mafft
```

After installation:

```bash
mafft --version
```

## License

MIT License. See [`LICENSE`](LICENSE).
