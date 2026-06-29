#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Installing KVM/libvirt virtualization stack"

dnf_install \
  @virtualization \
  qemu-kvm \
  libvirt \
  libvirt-daemon-config-network \
  libvirt-daemon-kvm \
  virt-install \
  virt-manager \
  virt-viewer \
  cockpit-machines \
  edk2-ovmf \
  swtpm \
  swtpm-tools

log "Enabling virtualization services"
enable_now libvirtd cockpit.socket

log "Adding $ADMIN_USER to virtualization groups"
for group in libvirt kvm; do
  if getent group "$group" >/dev/null; then
    usermod -aG "$group" "$ADMIN_USER"
  fi
done

log "Ensuring libvirt default NAT network is available"
if ! virsh net-info default >/dev/null 2>&1; then
  virsh net-define /usr/share/libvirt/networks/default.xml
fi
virsh net-autostart default
virsh net-start default >/dev/null 2>&1 || true

if systemctl is-active --quiet firewalld; then
  log "Opening Cockpit in firewalld"
  firewall-cmd --add-service=cockpit --permanent
  firewall-cmd --reload
else
  warn "firewalld is not active; skipping Cockpit firewall rule."
fi

log "Virtualization stack installed."
log "Log out and back in so $ADMIN_USER gets the libvirt/kvm group membership."
log "Cockpit Machines: https://$(hostname -I | awk '{print $1}'):9090"
log "Windows desktop client: install virt-viewer/Remote Viewer and open VM console files from Cockpit."
