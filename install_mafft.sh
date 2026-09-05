#!/usr/bin/env bash
set -Eeuo pipefail

# install_mafft.sh
# Best-effort MAFFT installer for macOS and common Linux distributions.
# It uses package managers already present on the system; it does not bootstrap
# Homebrew, Conda, or another package manager automatically.

ASSUME_YES=0
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: bash install_mafft.sh [--yes] [--dry-run] [--help]

Attempts to install MAFFT using a package manager already available on the
system, then verifies that `mafft` is on PATH.

Options:
  -y, --yes      Do not prompt before an install attempt.
  -n, --dry-run  Print detected methods and commands without executing them.
  -h, --help     Show this help message.

Supported install paths (when available):
  macOS/Linux: Homebrew
  Debian/Ubuntu: apt-get
  Fedora/RHEL-family: dnf or yum
  Arch-family: pacman
  openSUSE/SLES: zypper
  Cross-platform environments: micromamba, mamba, or conda (Bioconda)

This helper does not install package managers themselves.
EOF
}

while (($#)); do
  case "$1" in
    -y|--yes) ASSUME_YES=1 ;;
    -n|--dry-run) DRY_RUN=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

log()  { printf '[install_mafft] %s\n' "$*"; }
warn() { printf '[install_mafft] WARNING: %s\n' "$*" >&2; }

have() { command -v "$1" >/dev/null 2>&1; }

quote_cmd() {
  printf '  '
  printf '%q ' "$@"
  printf '\n'
}

confirm() {
  local prompt="$1"
  if (( ASSUME_YES )); then
    return 0
  fi
  if [[ ! -t 0 ]]; then
    warn "No interactive terminal available. Re-run with --yes to permit installation."
    return 1
  fi
  read -r -p "$prompt [y/N] " reply
  [[ "$reply" =~ ^[Yy]([Ee][Ss])?$ ]]
}

run_cmd() {
  log "Command:"
  quote_cmd "$@"
  if (( DRY_RUN )); then
    return 0
  fi
  "$@"
}

verify_mafft() {
  if have mafft; then
    log "MAFFT found at: $(command -v mafft)"
    # Different MAFFT builds may emit version information on stdout or stderr.
    mafft --version 2>&1 | head -n 2 || true
    return 0
  fi
  return 1
}

if verify_mafft; then
  log "Nothing to do."
  exit 0
fi

OS="$(uname -s 2>/dev/null || printf unknown)"
ARCH="$(uname -m 2>/dev/null || printf unknown)"
log "Detected platform: ${OS} ${ARCH}"

# Build candidate methods in platform-appropriate order. Homebrew is preferred
# on macOS; native distro package managers are preferred on Linux. Conda-family
# managers are retained as cross-platform fallbacks.
METHODS=()

case "$OS" in
  Darwin)
    have brew && METHODS+=(brew)
    ;;
  Linux)
    have apt-get && METHODS+=(apt)
    have dnf     && METHODS+=(dnf)
    have yum     && METHODS+=(yum)
    have pacman  && METHODS+=(pacman)
    have zypper  && METHODS+=(zypper)
    have brew    && METHODS+=(brew)
    ;;
  MINGW*|MSYS*|CYGWIN*)
    log "Windows-like shell detected. Native system-package installation is not attempted."
    ;;
  *)
    warn "Unrecognized operating system '${OS}'. Will try cross-platform package managers if present."
    ;;
esac

have micromamba && METHODS+=(micromamba)
have mamba      && METHODS+=(mamba)
have conda      && METHODS+=(conda)

if ((${#METHODS[@]} == 0)); then
  cat >&2 <<'EOF'
[install_mafft] ERROR: No supported package manager was found.

Install MAFFT manually, or first install one of the supported package managers.
Common choices are Homebrew on macOS or a Conda-compatible manager with
Bioconda configured.
EOF
  exit 1
fi

log "Available installation methods: ${METHODS[*]}"

need_privilege_prefix() {
  # Emit a NUL-safe-ish shell word list through global PREFIX array.
  PREFIX=()
  if [[ "$(id -u)" -ne 0 ]]; then
    if have sudo; then
      PREFIX=(sudo)
    else
      warn "This method normally requires root privileges, but sudo is unavailable."
      return 1
    fi
  fi
}

attempt_method() {
  local method="$1"
  local -a cmd=()

  case "$method" in
    brew)
      cmd=(brew install mafft)
      ;;
    apt)
      need_privilege_prefix || return 1
      if ! (( DRY_RUN )); then
        log "Refreshing apt package metadata first."
        run_cmd "${PREFIX[@]}" apt-get update || return 1
      else
        run_cmd "${PREFIX[@]}" apt-get update
      fi
      cmd=("${PREFIX[@]}" apt-get install -y mafft)
      ;;
    dnf)
      need_privilege_prefix || return 1
      cmd=("${PREFIX[@]}" dnf install -y mafft)
      ;;
    yum)
      need_privilege_prefix || return 1
      cmd=("${PREFIX[@]}" yum install -y mafft)
      ;;
    pacman)
      need_privilege_prefix || return 1
      cmd=("${PREFIX[@]}" pacman -S --needed --noconfirm mafft)
      ;;
    zypper)
      need_privilege_prefix || return 1
      cmd=("${PREFIX[@]}" zypper --non-interactive install mafft)
      ;;
    micromamba)
      cmd=(micromamba install -y -c conda-forge -c bioconda mafft)
      ;;
    mamba)
      cmd=(mamba install -y -c conda-forge -c bioconda mafft)
      ;;
    conda)
      cmd=(conda install -y -c conda-forge -c bioconda mafft)
      ;;
    *)
      return 1
      ;;
  esac

  log "Candidate method: $method"
  quote_cmd "${cmd[@]}"

  if (( DRY_RUN )); then
    return 0
  fi

  if ! confirm "Try installation with '$method'?"; then
    log "Skipped $method."
    return 1
  fi

  if run_cmd "${cmd[@]}"; then
    # Some package managers update shell state incompletely in the current
    # process; refresh Bash's command lookup cache before verification.
    hash -r 2>/dev/null || true
    if verify_mafft; then
      log "MAFFT installation succeeded using $method."
      return 0
    fi
    warn "$method completed, but 'mafft' is still not visible on PATH."
  else
    warn "$method failed."
  fi

  return 1
}

if (( DRY_RUN )); then
  log "Dry-run mode: showing all candidate commands."
  for method in "${METHODS[@]}"; do
    attempt_method "$method" || true
  done
  exit 0
fi

for method in "${METHODS[@]}"; do
  if attempt_method "$method"; then
    exit 0
  fi
done

cat >&2 <<'EOF'
[install_mafft] ERROR: All detected installation methods were exhausted.

MAFFT was not detected on PATH. Review the errors above and install MAFFT
manually using the appropriate method for your environment, then verify with:

  mafft --version
EOF
exit 1
