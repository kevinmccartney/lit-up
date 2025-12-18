#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "isort_format: $*" >&2
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_SCRIPTS_DIR="${ROOT_DIR}/projects/api/scripts"
VENV_PY="${API_SCRIPTS_DIR}/venv/bin/python"

if [[ $# -eq 0 ]]; then
  log "no files provided; skipping"
  exit 0
fi

# Filter to existing python files (lefthook should already scope, but be safe).
py_files=()
for f in "$@"; do
  if [[ -f "$f" && "$f" == *.py ]]; then
    py_files+=("$f")
  fi
done

if [[ ${#py_files[@]} -eq 0 ]]; then
  log "no python files to sort; skipping"
  exit 0
fi

runner=()
if [[ -x "$VENV_PY" ]]; then
  runner=("$VENV_PY" -m isort)
else
  # Fall back to system isort, if available.
  if command -v isort >/dev/null 2>&1; then
    runner=(isort)
  else
    log "✗ isort is not available"
    log "  expected venv python at: $VENV_PY"
    log "  fix by running:"
    log "    cd projects/api/scripts && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
  fi
fi

log "running isort on ${#py_files[@]} file(s)"
"${runner[@]}" --profile black "${py_files[@]}"

log "re-staging import-sorted files"
git add -- "${py_files[@]}"

log "✓ isort formatting complete"


