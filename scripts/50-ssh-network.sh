#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config
require_proxmox

log "Configuring SSH and Tailscale on Proxmox host"

apt_install openssh-server avahi-daemon libnss-mdns
systemctl enable --now ssh avahi-daemon

install -d -m 0755 /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/99-homelab.conf <<'EOF'
PermitRootLogin prohibit-password
PubkeyAuthentication yes
PasswordAuthentication yes
KbdInteractiveAuthentication no
X11Forwarding no
ClientAliveInterval 60
ClientAliveCountMax 3
EOF

if [[ -n "$SSH_AUTHORIZED_KEYS" && "$ADMIN_USER" != "root" ]]; then
  user_home="$(getent passwd "$ADMIN_USER" | cut -d: -f6 || true)"
  if [[ -n "$user_home" ]]; then
    install -d -m 0700 -o "$ADMIN_USER" -g "$ADMIN_USER" "$user_home/.ssh"
    printf '%s\n' "$SSH_AUTHORIZED_KEYS" >> "$user_home/.ssh/authorized_keys"
    chown "$ADMIN_USER":"$ADMIN_USER" "$user_home/.ssh/authorized_keys"
    chmod 0600 "$user_home/.ssh/authorized_keys"
  fi
fi

sshd -t
systemctl reload ssh

if [[ "$INSTALL_TAILSCALE" == "1" ]]; then
  if ! command -v tailscale >/dev/null 2>&1; then
    codename="$(. /etc/os-release && printf '%s' "$VERSION_CODENAME")"
    curl -fsSL "https://pkgs.tailscale.com/stable/debian/${codename}.noarmor.gpg" \
      -o /usr/share/keyrings/tailscale-archive-keyring.gpg
    curl -fsSL "https://pkgs.tailscale.com/stable/debian/${codename}.tailscale-keyring.list" \
      -o /etc/apt/sources.list.d/tailscale.list
    apt-get update
    apt_install tailscale
  fi
  enable_now tailscaled.service
  if [[ -n "$TAILSCALE_AUTHKEY" ]]; then
    tailscale up --authkey "$TAILSCALE_AUTHKEY" $TAILSCALE_EXTRA_ARGS
  else
    warn "Tailscale installed. Run: tailscale up $TAILSCALE_EXTRA_ARGS"
  fi
fi

log "Network addresses"
ip -brief address || true
