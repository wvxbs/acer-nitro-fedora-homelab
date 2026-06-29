#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Installing Minecraft Java and Bedrock homelab support"

dnf_install rclone zstd

install -d -m 0755 \
  "$APPDATA_DIR/minecraft-java" \
  "$APPDATA_DIR/minecraft-bedrock" \
  "$APPDATA_DIR/minecraft-backups/java" \
  "$APPDATA_DIR/minecraft-backups/bedrock"

chown -R "$ADMIN_USER":"$ADMIN_USER" \
  "$APPDATA_DIR/minecraft-java" \
  "$APPDATA_DIR/minecraft-bedrock" \
  "$APPDATA_DIR/minecraft-backups" || true

install -D -m 0755 "$ROOT/scripts/minecraft-backup.sh" /usr/local/sbin/nitro-minecraft-backup

cat > /etc/systemd/system/nitro-minecraft-backup.service <<EOF
[Unit]
Description=Back up Nitro Minecraft worlds to OneDrive
Wants=network-online.target docker.service
After=network-online.target docker.service

[Service]
Type=oneshot
Environment=NITRO_HOMELAB_REPO=$ROOT
Environment=HOMELAB_CONFIG=$ROOT/config/homelab.env
ExecStart=/usr/local/sbin/nitro-minecraft-backup
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=6
EOF

cat > /etc/systemd/system/nitro-minecraft-backup.timer <<EOF
[Unit]
Description=Daily Nitro Minecraft world backup

[Timer]
OnCalendar=*-*-* ${MINECRAFT_BACKUP_TIMER}:00
Persistent=true
RandomizedDelaySec=10m

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now nitro-minecraft-backup.timer

if command -v firewall-cmd >/dev/null 2>&1 && systemctl is-active --quiet firewalld; then
  firewall-cmd --add-port="${MINECRAFT_JAVA_PORT}/tcp" --permanent
  firewall-cmd --add-port="${MINECRAFT_BEDROCK_PORT}/udp" --permanent
  firewall-cmd --reload
fi

log "Minecraft support installed"
log "Start servers with: cd $HOMELAB_ROOT && docker compose --profile games up -d minecraft-java minecraft-bedrock"
log "Run a manual backup with: sudo systemctl start nitro-minecraft-backup.service"
