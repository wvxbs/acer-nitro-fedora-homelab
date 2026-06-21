#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Preparing local AI directories"

install -d -m 0755 "$OLLAMA_MODELS_DIR"
chown -R "$ADMIN_USER":"$ADMIN_USER" "$OLLAMA_MODELS_DIR" || true

log "AI profile is available in compose. Start with:"
log "cd $HOMELAB_ROOT && docker compose --profile ai up -d"
