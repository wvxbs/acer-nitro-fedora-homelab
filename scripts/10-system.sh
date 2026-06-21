#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config
require_proxmox

log "Proxmox host baseline"

hostnamectl set-hostname "$HOMELAB_HOSTNAME"
timedatectl set-timezone "$TZ"

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get full-upgrade -y
apt_install htop btop iotop iftop lm-sensors smartmontools hdparm nvme-cli lsof rsync tmux ethtool

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

log "Creating host directories"
install -d -m 0755 "$APPDATA_DIR" "$EXTERNAL_MOUNTPOINT" "$MEDIA_DIR" "$TRANSCODE_DIR" "$ONEDRIVE_LOCAL_PATH"

log "Enabling useful host services"
enable_now fstrim.timer || true
systemctl enable smartmontools.service || true
