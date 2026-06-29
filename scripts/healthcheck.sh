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
df -h "$APPDATA_DIR" "$STORAGE_ROOT" "$MEDIA_DIR" "$FILE_DROP_DIR" 2>/dev/null || df -h
lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS || true

log "Rclone"
rclone listremotes || true
docker ps --filter name=rclone-jellyfin --format '{{.Names}} {{.Status}}' || true
findmnt "$ONEDRIVE_MOUNT_PATH" || true
systemctl status rclone-onedrive-mount.service --no-pager || true

log "File Drop"
docker ps --filter name=file-drop --format '{{.Names}} {{.Status}}' || true
du -sh "$FILE_DROP_DIR" 2>/dev/null || true

log "Host Terminal"
docker ps --filter name=host-terminal --format '{{.Names}} {{.Status}}' || true
