#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "python_lint: $*" >&2
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_DIR="${ROOT_DIR}/projects/api"
API_SCRIPTS_DIR="${API_DIR}/scripts"
VENV_PY="${API_SCRIPTS_DIR}/venv/bin/python"

if [[ $# -eq 0 ]]; then
  log "no files provided; skipping"
  exit 0
fi

py_files=()
for f in "$@"; do
  if [[ -f "$f" && "$f" == projects/api/*.py ]]; then
    py_files+=("$f")
  elif [[ -f "$f" && "$f" == projects/api/**/*.py ]]; then
    py_files+=("$f")
  fi
done

if [[ ${#py_files[@]} -eq 0 ]]; then
  log "no python files to lint; skipping"
  exit 0
fi

have_venv=false
if [[ -x "$VENV_PY" ]]; then
  have_venv=true
fi

pylint_runner=()
flake8_runner=()

if [[ "$have_venv" == true ]]; then
  pylint_runner=("$VENV_PY" -m pylint)
  flake8_runner=("$VENV_PY" -m flake8)
else
  if command -v pylint >/dev/null 2>&1; then
    pylint_runner=(pylint)
  fi
  if command -v flake8 >/dev/null 2>&1; then
    flake8_runner=(flake8)
  fi

  if [[ ${#pylint_runner[@]} -eq 0 || ${#flake8_runner[@]} -eq 0 ]]; then
    log "✗ python linters are not available"
    log "  expected venv python at: $VENV_PY"
    log "  or system commands: pylint + flake8"
    log "  fix by running:"
    log "    cd projects/api/scripts && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
  fi
fi

log "running flake8 on ${#py_files[@]} file(s)"
(cd "$ROOT_DIR" && "${flake8_runner[@]}" --config "${API_DIR}/.flake8" "${py_files[@]}")
log "✓ flake8 passed"

log "running pylint on ${#py_files[@]} file(s)"
(cd "$ROOT_DIR" && "${pylint_runner[@]}" --rcfile "${API_DIR}/.pylintrc" "${py_files[@]}")
log "✓ pylint passed"


