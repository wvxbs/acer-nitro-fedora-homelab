#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
load_config

log "System"
hostnamectl || true
uptime || true

log "Network"
ip -brief address || true
tailscale status || true

log "Docker"
docker version || true
docker compose version || true

log "NVIDIA"
nvidia-smi || true
docker run --rm --gpus all nvidia/cuda:12.5.1-base-ubuntu22.04 nvidia-smi || true

log "Storage"
df -h "$APPDATA_DIR" "$EXTERNAL_MOUNTPOINT" "$MEDIA_DIR" 2>/dev/null || df -h
lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS || true

log "Rclone"
rclone listremotes || true
systemctl status rclone-onedrive-mount.service --no-pager || true
