#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib.sh
source "$ROOT/scripts/lib.sh"

require_root
load_config
require_proxmox

log "Starting Proxmox homelab bootstrap for $HOMELAB_HOSTNAME"

"$ROOT/scripts/00-preflight.sh"
"$ROOT/scripts/10-system.sh"
"$ROOT/scripts/40-storage.sh"
"$ROOT/scripts/50-ssh-network.sh"

if [[ "$INSTALL_NVIDIA" == "1" ]]; then
  "$ROOT/scripts/30-nvidia.sh"
else
  warn "Skipping NVIDIA host setup. Set INSTALL_NVIDIA=1 to enable it."
fi

"$ROOT/scripts/20-lxc-template.sh"
"$ROOT/scripts/70-services.sh"
"$ROOT/scripts/60-rclone.sh"

if [[ "$INSTALL_COMPOSE_BUNDLE" == "1" ]]; then
  "$ROOT/scripts/80-ai-local.sh"
else
  log "Skipping optional Compose bundle. Set INSTALL_COMPOSE_BUNDLE=1 to copy it to $HOMELAB_ROOT."
fi

log "Bootstrap complete. Reboot before final GPU validation."
log "After reboot: $ROOT/scripts/healthcheck.sh"
