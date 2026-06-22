#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Preparing per-user Codex delegation accounts"

if [[ -z "${CODEX_USERS// }" ]]; then
  log "CODEX_USERS is empty. Nothing to create."
  exit 0
fi

for user in $CODEX_USERS; do
  if ! [[ "$user" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
    warn "Skipping invalid Linux username: $user"
    continue
  fi

  if ! id -u "$user" >/dev/null 2>&1; then
    useradd -m -s /bin/bash "$user"
    passwd -l "$user" >/dev/null || true
    warn "Created $user with password login locked. Add SSH keys before remote use."
  else
    log "User $user already exists."
  fi

  install -d -m 0700 -o "$user" -g "$user" "/home/$user/.ssh"
  install -d -m 0700 -o "$user" -g "$user" "/home/$user/.codex"
  install -d -m 0755 -o "$user" -g "$user" "/home/$user/projects"
done

log "Codex users are isolated by Linux home directory and ~/.codex auth state."
log "Each person still needs their own SSH key and their own 'codex login --device-auth'."
