#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Configuring SSH, firewall, mDNS and Tailscale"

dnf_install openssh-server firewalld avahi nss-mdns
enable_now sshd.service firewalld.service avahi-daemon.service

firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-service=mdns
firewall-cmd --permanent --add-service=dns
firewall-cmd --permanent --add-port=32400/tcp
firewall-cmd --permanent --add-port=3000/tcp
firewall-cmd --permanent --add-port=3001/tcp
firewall-cmd --permanent --add-port=9443/tcp
firewall-cmd --permanent --add-port=9999/tcp
firewall-cmd --permanent --add-port=11434/tcp
firewall-cmd --permanent --add-service=samba
firewall-cmd --permanent --add-port=3702/udp
firewall-cmd --permanent --add-port=5357/tcp
firewall-cmd --reload

install -d -m 0755 /etc/avahi/services
cat > /etc/avahi/services/file-drop.service <<EOF
<?xml version="1.0" standalone='no'?><!--*-nxml-*-->
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">Nitro File Drop on %h</name>
  <service>
    <type>_smb._tcp</type>
    <port>445</port>
    <txt-record>path=/${FILE_DROP_SHARE_NAME}</txt-record>
  </service>
</service-group>
EOF
systemctl restart avahi-daemon.service || true

install -d -m 0755 /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/99-homelab.conf <<'EOF'
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication yes
KbdInteractiveAuthentication no
X11Forwarding no
ClientAliveInterval 60
ClientAliveCountMax 3
EOF

if [[ -n "${SSH_AUTHORIZED_KEYS:-}" ]]; then
  user_home="$(getent passwd "$ADMIN_USER" | cut -d: -f6)"
  install -d -m 0700 -o "$ADMIN_USER" -g "$ADMIN_USER" "$user_home/.ssh"
  printf '%s\n' "$SSH_AUTHORIZED_KEYS" >> "$user_home/.ssh/authorized_keys"
  chown "$ADMIN_USER":"$ADMIN_USER" "$user_home/.ssh/authorized_keys"
  chmod 0600 "$user_home/.ssh/authorized_keys"
fi

sshd -t
systemctl reload sshd

if [[ "$INSTALL_TAILSCALE" == "1" ]]; then
  dnf config-manager addrepo --from-repofile=https://pkgs.tailscale.com/stable/fedora/tailscale.repo
  dnf_install tailscale
  enable_now tailscaled.service

  if [[ -n "$TAILSCALE_AUTHKEY" ]]; then
    tailscale up --authkey "$TAILSCALE_AUTHKEY" $TAILSCALE_EXTRA_ARGS
  else
    warn "Tailscale installed. Run: sudo tailscale up $TAILSCALE_EXTRA_ARGS"
  fi
fi

log "Network addresses"
ip -brief address || true
