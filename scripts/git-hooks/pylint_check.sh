#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "pylint_check: $*" >&2
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_LINT="${ROOT_DIR}/scripts/git-hooks/python_lint.sh"

if [[ $# -eq 0 ]]; then
  log "no files provided; skipping"
  exit 0
fi

log "deprecated: use scripts/git-hooks/python_lint.sh (runs flake8 + pylint)"
exec "$PYTHON_LINT" "$@"


