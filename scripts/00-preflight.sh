#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config
require_proxmox

log "Preflight checks"

apt-get update
apt_install curl ca-certificates gnupg lsb-release git nano vim bash-completion tar unzip jq pciutils usbutils

log "Proxmox: $(pveversion)"
log "Debian: $(. /etc/os-release && printf '%s %s' "$PRETTY_NAME" "$VERSION_CODENAME")"
log "Kernel: $(uname -r)"

if ! grep -qw vmx /proc/cpuinfo; then
  warn "Intel VT-x flag 'vmx' not found. Check BIOS virtualization settings."
fi

log "PCI GPU devices"
lspci -nn | grep -Ei 'vga|3d|display|nvidia' || warn "No GPU listed by lspci."

log "Block devices"
lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS || true
