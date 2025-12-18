#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "infra_terraform_checks: $*" >&2
}

if ! command -v terraform >/dev/null 2>&1; then
  log "✗ terraform not found in PATH"
  exit 1
fi

if ! command -v tflint >/dev/null 2>&1; then
  log "✗ tflint not found in PATH"
  log "  install: https://github.com/terraform-linters/tflint#installation"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INFRA_DIR="${ROOT_DIR}/projects/infra"

if [[ ! -d "$INFRA_DIR" ]]; then
  log "✗ infra directory not found: $INFRA_DIR"
  exit 1
fi

log "running terraform fmt check (recursive)"
(cd "$INFRA_DIR" && terraform fmt -check -diff -recursive)

log "running tflint"
(
  cd "$INFRA_DIR"
  # If plugins are not initialized yet, this will fail with a helpful error.
  # Run once: tflint --init
  tflint --recursive
)

log "✓ infra terraform checks passed"

