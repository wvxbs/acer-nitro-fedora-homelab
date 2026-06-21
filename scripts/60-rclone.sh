#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config
require_proxmox

log "Configuring rclone pull-only timer inside media CT"

pct_exists "$MEDIA_CT_ID" || die "CT $MEDIA_CT_ID does not exist. Run scripts/70-services.sh first."
pct_is_running "$MEDIA_CT_ID" || pct start "$MEDIA_CT_ID"

pct_exec install -d -m 0755 /var/log/rclone /incoming/onedrive
pct_exec chown -R "$RCLONE_USER":"$RCLONE_USER" /var/log/rclone /incoming/onedrive || true

bwlimit_arg=""
if [[ -n "$RCLONE_BWLIMIT" ]]; then
  bwlimit_arg="--bwlimit $RCLONE_BWLIMIT"
fi

pct_exec bash -lc "cat > /etc/systemd/system/rclone-onedrive-pull.service" <<EOF
[Unit]
Description=Pull OneDrive DVD rips to local storage with rclone
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
User=$RCLONE_USER
Group=$RCLONE_USER
ExecStart=/usr/bin/rclone sync "$RCLONE_REMOTE_NAME:$ONEDRIVE_PATH" "/incoming/onedrive" --create-empty-src-dirs --fast-list --transfers 2 --checkers 4 --log-file /var/log/rclone/onedrive-pull.log --log-level INFO $bwlimit_arg
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=6
EOF

pct_exec bash -lc "cat > /etc/systemd/system/rclone-onedrive-pull.timer" <<EOF
[Unit]
Description=Schedule OneDrive pull-only sync

[Timer]
OnCalendar=$RCLONE_SCHEDULE
Persistent=true
RandomizedDelaySec=120

[Install]
WantedBy=timers.target
EOF

pct_exec systemctl daemon-reload
warn "Run 'rclone config' as $RCLONE_USER inside CT $MEDIA_CT_ID before enabling rclone-onedrive-pull.timer."
