#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config
require_proxmox

log "Preparing Proxmox LXC template"

pveam update
mapfile -t templates < <(pveam available --section system | awk -v rel="debian-${DEBIAN_CT_RELEASE}-standard" '$2 ~ rel && $2 ~ /amd64/ {print $2}' | sort -V)
if [[ "${#templates[@]}" -eq 0 ]]; then
  die "No Debian ${DEBIAN_CT_RELEASE} amd64 standard template found in pveam. Run 'pveam available --section system' to inspect options."
fi

template="${templates[-1]}"
if ! pveam list "$MEDIA_CT_STORAGE" | awk '{print $1}' | grep -qx "$template"; then
  log "Downloading $template to $MEDIA_CT_STORAGE"
  pveam download "$MEDIA_CT_STORAGE" "$template"
else
  log "Template already present: $template"
fi
