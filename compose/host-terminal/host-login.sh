#!/usr/bin/env bash
set -euo pipefail

exec nsenter \
  --target 1 \
  --mount \
  --uts \
  --ipc \
  --net \
  --pid \
  --wd=/ \
  -- /bin/login
