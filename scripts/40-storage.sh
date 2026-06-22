#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Configuring storage"

install -d -m 0755 "$STORAGE_ROOT" "$MEDIA_DIR" "$ONEDRIVE_MOUNT_PATH" "$APPDATA_DIR" "$RCLONE_CACHE_DIR"

chown -R "$ADMIN_USER":"$ADMIN_USER" "$APPDATA_DIR" "$STORAGE_ROOT" || true

log "Current block devices"
lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS || true
