#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "eslint_ui_check: $*" >&2
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UI_DIR="${ROOT_DIR}/projects/ui"

if [[ ! -d "$UI_DIR" ]]; then
  log "ui directory not found at: $UI_DIR"
  exit 1
fi

log "running eslint (no auto-fix)"
(cd "$UI_DIR" && npm run -s lint)

log "✓ eslint passed"


