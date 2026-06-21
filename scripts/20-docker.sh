#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Installing Docker Engine"

if [[ ! -f /etc/yum.repos.d/docker-ce.repo ]]; then
  dnf config-manager addrepo --from-repofile=https://download.docker.com/linux/fedora/docker-ce.repo
else
  log "Docker repo already configured"
fi
dnf_install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

install -d -m 0755 /etc/docker
cat > /etc/docker/daemon.json <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "features": {
    "buildkit": true
  }
}
EOF

usermod -aG docker "$ADMIN_USER" || true
enable_now docker.service

log "Docker installed. User $ADMIN_USER may need to log out/in for docker group membership."
