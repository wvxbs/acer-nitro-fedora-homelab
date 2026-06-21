#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
load_config

log "Proxmox host"
pveversion || true
hostnamectl || true
uptime || true

log "Network"
ip -brief address || true
tailscale status || true

log "NVIDIA host"
lsmod | grep -E '^nvidia' || true
nvidia-smi || true

log "Media CT"
pct status "$MEDIA_CT_ID" || true
pct config "$MEDIA_CT_ID" || true
if pct_is_running "$MEDIA_CT_ID"; then
  pct exec "$MEDIA_CT_ID" -- hostname -I || true
  pct exec "$MEDIA_CT_ID" -- nvidia-smi || true
  pct exec "$MEDIA_CT_ID" -- systemctl --no-pager --full status plexmediaserver || true
  pct exec "$MEDIA_CT_ID" -- systemctl list-timers rclone-onedrive-pull.timer || true
fi

log "Storage"
df -h "$APPDATA_DIR" "$EXTERNAL_MOUNTPOINT" "$MEDIA_DIR" 2>/dev/null || df -h
lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS || true
