#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Installing homelab compose bundle"

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

chown -R "$ADMIN_USER":"$ADMIN_USER" "$HOMELAB_ROOT"

log "Compose files installed at $HOMELAB_ROOT"
log "Start media stack with: cd $HOMELAB_ROOT && docker compose --profile media up -d"
