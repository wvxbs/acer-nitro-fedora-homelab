#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "System baseline"

hostnamectl set-hostname "$HOMELAB_HOSTNAME"
timedatectl set-timezone "$TZ"

dnf upgrade -y --refresh
dnf_install htop btop iotop iftop lm_sensors smartmontools hdparm nvme-cli usbutils pciutils lsof jq rsync tmux

log "Preventing suspend when the lid closes"
install -d -m 0755 /etc/systemd/logind.conf.d
cat > /etc/systemd/logind.conf.d/99-homelab-lid.conf <<'EOF'
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
IdleAction=ignore
EOF
systemctl restart systemd-logind || true

log "Creating service directories"
install -d -m 0755 "$APPDATA_DIR" "$EXTERNAL_MOUNTPOINT" "$MEDIA_DIR" "$TRANSCODE_DIR" "$HOMELAB_ROOT"
chown -R "$ADMIN_USER":"$ADMIN_USER" "$APPDATA_DIR" "$HOMELAB_ROOT" || true

log "Enabling useful services"
enable_now systemd-timesyncd.service || true
enable_now fstrim.timer || true
systemctl enable smartd.service || true

