#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config
require_proxmox

log "Installing NVIDIA driver on Proxmox host"

if mokutil --sb-state 2>/dev/null | grep -qi enabled; then
  warn "Secure Boot appears enabled. NVIDIA DKMS modules may not load unless you sign/enroll them. Lowest-friction path: disable Secure Boot."
fi

codename="$(. /etc/os-release && printf '%s' "$VERSION_CODENAME")"
cat > /etc/apt/sources.list.d/debian-nonfree.sources <<EOF
Types: deb
URIs: http://deb.debian.org/debian
Suites: $codename ${codename}-updates
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: http://security.debian.org/debian-security
Suites: ${codename}-security
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
EOF

apt-get update
apt_install build-essential dkms
if ! apt-get install -y "proxmox-headers-$(uname -r)"; then
  if ! apt-get install -y "pve-headers-$(uname -r)"; then
    apt_install pve-headers || warn "Could not install exact Proxmox headers automatically. Check apt repositories before NVIDIA DKMS build."
  fi
fi
apt_install nvidia-driver nvidia-smi nvidia-modprobe firmware-misc-nonfree vainfo

install -d -m 0755 /etc/modules-load.d
cat > /etc/modules-load.d/nvidia-homelab.conf <<'EOF'
nvidia
nvidia_uvm
nvidia_modeset
nvidia_drm
EOF

modprobe nvidia || warn "nvidia module did not load yet. A reboot is likely required."
modprobe nvidia_uvm || true
nvidia-modprobe -u -c=0 || true

nvidia-smi || warn "nvidia-smi failed. Reboot, then rerun scripts/healthcheck.sh."
