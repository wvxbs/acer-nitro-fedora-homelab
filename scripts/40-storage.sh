#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Configuring storage"

install -d -m 0755 "$EXTERNAL_MOUNTPOINT" "$MEDIA_DIR" "$ONEDRIVE_MOUNT_PATH" "$APPDATA_DIR" "$TRANSCODE_DIR" "$RCLONE_CACHE_DIR"

if [[ -n "$EXTERNAL_DISK_UUID" ]]; then
  if ! grep -q "$EXTERNAL_DISK_UUID" /etc/fstab; then
    printf 'UUID=%s %s %s defaults,nofail,x-systemd.device-timeout=15 0 2\n' \
      "$EXTERNAL_DISK_UUID" "$EXTERNAL_MOUNTPOINT" "$EXTERNAL_DISK_FSTYPE" >> /etc/fstab
  fi
  mount "$EXTERNAL_MOUNTPOINT" || warn "Could not mount $EXTERNAL_MOUNTPOINT yet. Check UUID/filesystem."
else
  warn "EXTERNAL_DISK_UUID is empty. Skipping fstab entry."
fi

chown -R "$ADMIN_USER":"$ADMIN_USER" "$APPDATA_DIR" "$EXTERNAL_MOUNTPOINT" || true

log "Current block devices"
lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS || true
