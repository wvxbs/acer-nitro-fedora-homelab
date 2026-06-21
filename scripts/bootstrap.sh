#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib.sh
source "$ROOT/scripts/lib.sh"

require_root
load_config

log "Starting Fedora homelab bootstrap for $HOMELAB_HOSTNAME"

"$ROOT/scripts/00-preflight.sh"
"$ROOT/scripts/10-system.sh"
"$ROOT/scripts/20-docker.sh"
"$ROOT/scripts/30-nvidia.sh"
"$ROOT/scripts/40-storage.sh"
"$ROOT/scripts/50-ssh-network.sh"
"$ROOT/scripts/60-rclone.sh"
"$ROOT/scripts/70-services.sh"

if [[ "$INSTALL_AI" == "1" ]]; then
  "$ROOT/scripts/80-ai-local.sh"
else
  log "Skipping AI profile. Set INSTALL_AI=1 in config/homelab.env to enable it."
fi

log "Bootstrap complete. Reboot before validating NVIDIA containers."
log "After reboot: $ROOT/scripts/healthcheck.sh"
