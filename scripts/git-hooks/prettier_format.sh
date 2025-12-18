#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "prettier_format: $*" >&2
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ $# -eq 0 ]]; then
  log "no files provided; skipping"
  exit 0
fi

if ! command -v prettier >/dev/null 2>&1; then
  log "✗ prettier is not available (expected global install)"
  log "  install with:"
  log "    npm i -g prettier"
  exit 1
fi

supported_files=()
for f in "$@"; do
  if [[ ! -f "$f" ]]; then
    continue
  fi

  case "$f" in
    *.js|*.jsx|*.ts|*.tsx|*.json|*.yml|*.yaml|*.md|*.mdx|*.css|*.scss|*.html)
      supported_files+=("$f")
      ;;
    *)
      ;;
  esac
done

if [[ ${#supported_files[@]} -eq 0 ]]; then
  log "no supported files to format; skipping"
  exit 0
fi

log "running prettier on ${#supported_files[@]} file(s)"
(cd "$ROOT_DIR" && prettier --write --ignore-unknown --ignore-path "$ROOT_DIR/.prettierignore" -- "${supported_files[@]}")

log "re-staging formatted files"
git add -- "${supported_files[@]}"

log "✓ prettier formatting complete"


