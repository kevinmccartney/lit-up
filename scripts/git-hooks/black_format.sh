#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "black_format: $*" >&2
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
  log "no python files to format; skipping"
  exit 0
fi

runner=()
if [[ -x "$VENV_PY" ]]; then
  runner=("$VENV_PY" -m black)
else
  # Fall back to system black, if available.
  if command -v black >/dev/null 2>&1; then
    runner=(black)
  else
    log "✗ black is not available"
    log "  expected venv python at: $VENV_PY"
    log "  fix by running:"
    log "    cd projects/api/scripts && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
  fi
fi

log "running black on ${#py_files[@]} file(s)"
"${runner[@]}" "${py_files[@]}"

log "re-staging formatted files"
git add -- "${py_files[@]}"

log "✓ black formatting complete"


