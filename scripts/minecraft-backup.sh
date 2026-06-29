#!/usr/bin/env bash
set -euo pipefail

ROOT="${NITRO_HOMELAB_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
source "$ROOT/scripts/lib.sh"
load_config

COMPOSE_DIR="${HOMELAB_ROOT:-/opt/homelab}"
LOCAL_BACKUP_DIR="${APPDATA_DIR}/minecraft-backups"
STAMP="$(date +'%Y%m%d-%H%M%S')"
JAVA_LEVEL="${MINECRAFT_JAVA_LEVEL_NAME:-Nitro-Java}"
BEDROCK_LEVEL="${MINECRAFT_BEDROCK_LEVEL_NAME:-Nitro-Bedrock}"
REMOTE_BASE="${RCLONE_REMOTE_NAME}:${MINECRAFT_BACKUP_REMOTE_PATH}"

log "Starting Minecraft backup ${STAMP}"

install -d -m 0755 "$LOCAL_BACKUP_DIR/java" "$LOCAL_BACKUP_DIR/bedrock"

if [[ -d "$COMPOSE_DIR" ]]; then
  log "Stopping Minecraft containers for a consistent world snapshot"
  docker compose --profile games --project-directory "$COMPOSE_DIR" -f "$COMPOSE_DIR/docker-compose.yml" stop minecraft-java minecraft-bedrock
fi

restart_servers() {
  if [[ -d "$COMPOSE_DIR" ]]; then
    log "Starting Minecraft containers"
    docker compose --profile games --project-directory "$COMPOSE_DIR" -f "$COMPOSE_DIR/docker-compose.yml" up -d minecraft-java minecraft-bedrock
  fi
}
trap restart_servers EXIT

JAVA_WORLD_DIR="${APPDATA_DIR}/minecraft-java/${JAVA_LEVEL}"
BEDROCK_WORLD_DIR="${APPDATA_DIR}/minecraft-bedrock/worlds/${BEDROCK_LEVEL}"

if [[ -d "$JAVA_WORLD_DIR" ]]; then
  JAVA_ARCHIVE="${LOCAL_BACKUP_DIR}/java/${JAVA_LEVEL}-${STAMP}.tar.zst"
  log "Archiving Java world: $JAVA_WORLD_DIR"
  tar --use-compress-program zstd -cpf "$JAVA_ARCHIVE" -C "$(dirname "$JAVA_WORLD_DIR")" "$(basename "$JAVA_WORLD_DIR")"
else
  warn "Java world directory not found yet: $JAVA_WORLD_DIR"
fi

if [[ -d "$BEDROCK_WORLD_DIR" ]]; then
  BEDROCK_ARCHIVE="${LOCAL_BACKUP_DIR}/bedrock/${BEDROCK_LEVEL}-${STAMP}.tar.zst"
  log "Archiving Bedrock world: $BEDROCK_WORLD_DIR"
  tar --use-compress-program zstd -cpf "$BEDROCK_ARCHIVE" -C "$(dirname "$BEDROCK_WORLD_DIR")" "$(basename "$BEDROCK_WORLD_DIR")"
else
  warn "Bedrock world directory not found yet: $BEDROCK_WORLD_DIR"
fi

if [[ "${MINECRAFT_BACKUP_ONEDRIVE:-1}" == "1" ]]; then
  log "Uploading Minecraft backups to OneDrive"
  rclone mkdir "${REMOTE_BASE}/Java" --config "$RCLONE_CONFIG_PATH"
  rclone mkdir "${REMOTE_BASE}/Bedrock" --config "$RCLONE_CONFIG_PATH"
  rclone copy "${LOCAL_BACKUP_DIR}/java" "${REMOTE_BASE}/Java" --config "$RCLONE_CONFIG_PATH" --transfers 2 --checkers 4 --fast-list
  rclone copy "${LOCAL_BACKUP_DIR}/bedrock" "${REMOTE_BASE}/Bedrock" --config "$RCLONE_CONFIG_PATH" --transfers 2 --checkers 4 --fast-list
fi

find "${LOCAL_BACKUP_DIR}/java" -type f -name '*.tar.zst' -mtime "+${MINECRAFT_BACKUP_KEEP_LOCAL_DAYS:-7}" -delete
find "${LOCAL_BACKUP_DIR}/bedrock" -type f -name '*.tar.zst' -mtime "+${MINECRAFT_BACKUP_KEEP_LOCAL_DAYS:-7}" -delete

trap - EXIT
restart_servers

log "Minecraft backup complete"
