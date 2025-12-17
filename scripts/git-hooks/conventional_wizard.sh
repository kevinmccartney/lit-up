#!/usr/bin/env bash
set -euo pipefail

# Conventional Commit wizard for prepare-commit-msg.
#
# Git passes:
#   $1: path to commit message file
#   $2: commit source (optional) (e.g. message, template, merge, squash, commit)
#   $3: SHA-1 (optional)
#
# We only run interactively (TTY) and we avoid clobbering messages that are
# already populated (e.g. -m, merges, squashes, etc.).

MSG_FILE="${1:-}"
SOURCE="${2:-}"

if [[ -z "$MSG_FILE" ]]; then
  exit 0
fi

# Skip non-interactive environments.
if [[ ! -t 0 && ! -t 1 ]]; then
  exit 0
fi

# Skip commits where Git generated or provided a message.
case "${SOURCE:-}" in
  message|template|merge|squash|commit)
    exit 0
    ;;
esac

# If the message already has a non-comment first line, don't overwrite it.
if [[ -f "$MSG_FILE" ]]; then
  existing_first_line="$(grep -v '^[[:space:]]*#' "$MSG_FILE" | head -n 1 || true)"
  if [[ -n "${existing_first_line:-}" ]]; then
    exit 0
  fi
fi

TYPES=("feat" "fix" "docs" "style" "refactor" "perf" "test" "build" "ci" "chore" "revert")

prompt() {
  local question="$1"
  local default="${2:-}"
  local value=""
  if [[ -n "$default" ]]; then
    read -r -p "${question} [${default}]: " value < /dev/tty || true
    echo "${value:-$default}"
  else
    read -r -p "${question}: " value < /dev/tty || true
    echo "$value"
  fi
}

select_type() {
  echo "Select commit type:" > /dev/tty
  local i=1
  for t in "${TYPES[@]}"; do
    echo "  $i) $t" > /dev/tty
    i=$((i + 1))
  done
  local choice
  while true; do
    choice="$(prompt "Type number" "1")"
    if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#TYPES[@]} )); then
      echo "${TYPES[$((choice - 1))]}"
      return 0
    fi
    echo "Invalid choice. Enter a number 1-${#TYPES[@]}." > /dev/tty
  done
}

type="$(select_type)"
scope="$(prompt "Scope (optional, no spaces)" "")"
breaking="$(prompt "Breaking change? (y/N)" "N")"
subject=""
while [[ -z "$subject" ]]; do
  subject="$(prompt "Subject (required, imperative, no trailing period)" "")"
  subject="$(echo "$subject" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
done

bang=""
if [[ "${breaking,,}" == "y" || "${breaking,,}" == "yes" ]]; then
  bang="!"
fi

header="$type"
if [[ -n "$scope" ]]; then
  header="${header}(${scope})"
fi
header="${header}${bang}: ${subject}"

body="$(prompt "Body (optional; leave blank)" "")"
footer="$(prompt "Footer (optional; e.g. BREAKING CHANGE: ... or refs)" "")"

{
  echo "$header"
  echo
  if [[ -n "$body" ]]; then
    echo "$body"
    echo
  fi
  if [[ -n "$footer" ]]; then
    echo "$footer"
    echo
  fi
} > "$MSG_FILE"

echo "Wrote Conventional Commit message:" > /dev/tty
echo "  $header" > /dev/tty

