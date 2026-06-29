#!/usr/bin/env bash
set -euo pipefail

DROP_PATH="${DROP_PATH:-/drop}"
TTL_HOURS="${FILE_DROP_TTL_HOURS:-24}"
MAX_SIZE="${FILE_DROP_MAX_SIZE:-100G}"
SLEEP_SECONDS="${FILE_DROP_CLEANUP_INTERVAL_SECONDS:-300}"
GUEST_USER="${FILE_DROP_GUEST_USER:-filedrop}"

to_bytes() {
  local value number suffix multiplier
  value="$1"
  suffix="${value: -1}"

  case "$suffix" in
    K|k) number="${value%?}"; multiplier=1024 ;;
    M|m) number="${value%?}"; multiplier=$((1024 * 1024)) ;;
    G|g) number="${value%?}"; multiplier=$((1024 * 1024 * 1024)) ;;
    T|t) number="${value%?}"; multiplier=$((1024 * 1024 * 1024 * 1024)) ;;
    *) number="$value"; multiplier=1 ;;
  esac

  awk -v n="$number" -v m="$multiplier" 'BEGIN { printf "%.0f", n * m }'
}

current_bytes() {
  find "$DROP_PATH" -mindepth 1 \
    -type f \
    ! -name '.DS_Store' \
    ! -name '._*' \
    ! -name 'Thumbs.db' \
    ! -name 'desktop.ini' \
    -printf '%s\n' 2>/dev/null \
    | awk '{ total += $1 } END { print total + 0 }'
}

prune_metadata() {
  find "$DROP_PATH" -mindepth 1 \( \
    -name '.DS_Store' -o \
    -name '._*' -o \
    -name 'Thumbs.db' -o \
    -name 'desktop.ini' \
  \) -exec rm -rf -- {} + 2>/dev/null || true
}

prune_by_age() {
  local ttl_minutes
  ttl_minutes=$((TTL_HOURS * 60))
  find "$DROP_PATH" -mindepth 1 \
    ! -name '.DS_Store' \
    ! -name '._*' \
    ! -name 'Thumbs.db' \
    ! -name 'desktop.ini' \
    -mmin +"$ttl_minutes" -exec rm -rf -- {} + 2>/dev/null || true
}

prune_by_size() {
  local max_bytes current oldest
  max_bytes="$(to_bytes "$MAX_SIZE")"
  current="$(current_bytes)"

  while [[ "$current" -gt "$max_bytes" ]]; do
    oldest="$(find "$DROP_PATH" -mindepth 1 -maxdepth 1 -printf '%T@ %p\n' 2>/dev/null | sort -n | head -n 1 | cut -d ' ' -f 2-)"
    [[ -n "$oldest" ]] || break
    rm -rf -- "$oldest"
    current="$(current_bytes)"
  done
}

while true; do
  install -d -m 0777 -o "$GUEST_USER" -g "$GUEST_USER" "$DROP_PATH" 2>/dev/null || install -d -m 0777 "$DROP_PATH"
  prune_metadata
  prune_by_age
  prune_by_size
  sleep "$SLEEP_SECONDS"
done
