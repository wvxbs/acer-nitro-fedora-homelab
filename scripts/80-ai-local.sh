#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config
require_proxmox

log "Installing optional Compose bundle for non-GPU workloads"

apt_install rsync
install -d -m 0755 "$HOMELAB_ROOT"
rsync -a --delete "$ROOT/compose/" "$HOMELAB_ROOT/"

cat > "$HOMELAB_ROOT/.env" <<EOF
PUID=$PUID
PGID=$PGID
TZ=$TZ
APPDATA_DIR=$APPDATA_DIR
MEDIA_DIR=$MEDIA_DIR
TRANSCODE_DIR=$TRANSCODE_DIR
PLEX_CLAIM=$PLEX_CLAIM
PLEX_ADVERTISE_IP=$PLEX_ADVERTISE_IP
OLLAMA_MODELS_DIR=$OLLAMA_MODELS_DIR
EOF

log "Compose files copied to $HOMELAB_ROOT. Run Docker in a dedicated VM/CT unless you intentionally want Docker on the Proxmox host."
