#!/usr/bin/env bash
set -euo pipefail

workdir="${TERMINAL_WORKDIR:-/root}"
shell_path="${TERMINAL_SHELL:-/bin/bash}"

exec nsenter \
  --target 1 \
  --mount \
  --uts \
  --ipc \
  --net \
  --pid \
  --wd="$workdir" \
  -- "$shell_path" -l
