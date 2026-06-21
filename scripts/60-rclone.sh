#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Installing rclone and pull-only OneDrive timer"

dnf_install rclone

install -d -m 0755 "$ONEDRIVE_LOCAL_PATH" /var/log/rclone
chown -R "$RCLONE_USER":"$RCLONE_USER" "$ONEDRIVE_LOCAL_PATH" /var/log/rclone || true

cat > /etc/systemd/system/rclone-onedrive-pull.service <<EOF
[Unit]
Description=Pull OneDrive DVD rips to local storage with rclone
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
User=$RCLONE_USER
Group=$RCLONE_USER
ExecStart=/usr/bin/rclone sync "$RCLONE_REMOTE_NAME:$ONEDRIVE_PATH" "$ONEDRIVE_LOCAL_PATH" --create-empty-src-dirs --fast-list --transfers 2 --checkers 4 --log-file /var/log/rclone/onedrive-pull.log --log-level INFO ${RCLONE_BWLIMIT:+--bwlimit $RCLONE_BWLIMIT}
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=6
EOF

cat > /etc/systemd/system/rclone-onedrive-pull.timer <<EOF
[Unit]
Description=Schedule OneDrive pull-only sync

[Timer]
OnCalendar=$RCLONE_SCHEDULE
Persistent=true
RandomizedDelaySec=120

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload

warn "Run 'rclone config' as $RCLONE_USER before enabling rclone-onedrive-pull.timer."
