#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Preflight checks"

if [[ ! -f /etc/fedora-release ]]; then
  die "This bootstrap targets Fedora Server."
fi

dnf_install dnf-plugins-core curl ca-certificates git nano vim bash-completion tar unzip policycoreutils-python-utils

log "Fedora release: $(cat /etc/fedora-release)"
log "Kernel: $(uname -r)"
log "Disks:"
lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS || true
