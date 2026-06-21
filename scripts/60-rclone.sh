#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Installing rclone OneDrive mount for local media servers"

dnf_install rclone fuse3

install -d -m 0755 "$ONEDRIVE_MOUNT_PATH" "$RCLONE_CACHE_DIR" /var/log/rclone
chown -R "$RCLONE_USER":"$RCLONE_USER" "$ONEDRIVE_MOUNT_PATH" "$RCLONE_CACHE_DIR" /var/log/rclone || true

if ! grep -q '^user_allow_other$' /etc/fuse.conf 2>/dev/null; then
  printf '\nuser_allow_other\n' >> /etc/fuse.conf
fi

cat > /etc/systemd/system/rclone-onedrive-mount.service <<EOF
[Unit]
Description=Mount OneDrive media with bounded rclone VFS cache
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=$RCLONE_USER
Group=$RCLONE_USER
ExecStartPre=/usr/bin/mkdir -p "$ONEDRIVE_MOUNT_PATH" "$RCLONE_CACHE_DIR"
ExecStart=/usr/bin/rclone mount "$RCLONE_REMOTE_NAME:$ONEDRIVE_PATH" "$ONEDRIVE_MOUNT_PATH" \\
  --config "$RCLONE_CONFIG_PATH" \\
  --read-only \\
  --allow-other \\
  --dir-cache-time 12h \\
  --poll-interval 1m \\
  --vfs-cache-mode full \\
  --vfs-cache-max-size "$RCLONE_VFS_CACHE_MAX_SIZE" \\
  --vfs-cache-max-age "$RCLONE_VFS_CACHE_MAX_AGE" \\
  --vfs-cache-min-free-space "$RCLONE_VFS_CACHE_MIN_FREE_SPACE" \\
  --vfs-read-chunk-size 64M \\
  --vfs-read-chunk-size-limit 1G \\
  --buffer-size "$RCLONE_BUFFER_SIZE" \\
  --cache-dir "$RCLONE_CACHE_DIR" \\
  --transfers 2 \\
  --checkers 4 \\
  --log-file /var/log/rclone/onedrive-mount.log \\
  --log-level INFO
ExecStop=/usr/bin/fusermount3 -uz "$ONEDRIVE_MOUNT_PATH"
Restart=on-failure
RestartSec=15
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=6

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

warn "Run 'rclone config' as $RCLONE_USER, validate with 'rclone lsd $RCLONE_REMOTE_NAME:', then start the media Compose profile or enable rclone-onedrive-mount.service."
