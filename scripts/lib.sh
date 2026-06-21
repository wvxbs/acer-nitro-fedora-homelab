#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '\n[%s] %s\n' "$(date +'%H:%M:%S')" "$*"
}

warn() {
  printf '\n[WARN] %s\n' "$*" >&2
}

die() {
  printf '\n[ERROR] %s\n' "$*" >&2
  exit 1
}

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    die "Run as root: sudo $0"
  fi
}

repo_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
}

load_config() {
  local root config
  root="$(repo_root)"
  config="${HOMELAB_CONFIG:-$root/config/homelab.env}"

  if [[ -f "$config" ]]; then
    # shellcheck disable=SC1090
    set -a
    source "$config"
    set +a
  else
    warn "Config file not found: $config. Using defaults from scripts."
  fi

  HOMELAB_HOSTNAME="${HOMELAB_HOSTNAME:-nitro-homelab}"
  ADMIN_USER="${ADMIN_USER:-${SUDO_USER:-$(id -un)}}"
  INSTALL_TAILSCALE="${INSTALL_TAILSCALE:-1}"
  TAILSCALE_AUTHKEY="${TAILSCALE_AUTHKEY:-}"
  TAILSCALE_EXTRA_ARGS="${TAILSCALE_EXTRA_ARGS:---ssh}"
  STORAGE_ROOT="${STORAGE_ROOT:-/srv/storage}"
  RCLONE_REMOTE_NAME="${RCLONE_REMOTE_NAME:-onedrive}"
  ONEDRIVE_PATH="${ONEDRIVE_PATH:-Vídeos/Filmes}"
  ONEDRIVE_MOUNT_PATH="${ONEDRIVE_MOUNT_PATH:-$STORAGE_ROOT/media/onedrive}"
  RCLONE_CONFIG_PATH="${RCLONE_CONFIG_PATH:-/home/$ADMIN_USER/.config/rclone/rclone.conf}"
  RCLONE_CACHE_DIR="${RCLONE_CACHE_DIR:-/srv/appdata/rclone/vfs-cache}"
  RCLONE_VFS_CACHE_MAX_SIZE="${RCLONE_VFS_CACHE_MAX_SIZE:-40G}"
  RCLONE_VFS_CACHE_MAX_AGE="${RCLONE_VFS_CACHE_MAX_AGE:-12h}"
  RCLONE_VFS_CACHE_MIN_FREE_SPACE="${RCLONE_VFS_CACHE_MIN_FREE_SPACE:-30G}"
  RCLONE_BUFFER_SIZE="${RCLONE_BUFFER_SIZE:-64M}"
  RCLONE_USER="${RCLONE_USER:-$ADMIN_USER}"
  RCLONE_BWLIMIT="${RCLONE_BWLIMIT:-}"
  RCLONE_JELLYFIN_IMAGE="${RCLONE_JELLYFIN_IMAGE:-wvxbs/rclone-jellyfin:latest}"
  HOMELAB_ROOT="${HOMELAB_ROOT:-/opt/homelab}"
  APPDATA_DIR="${APPDATA_DIR:-/srv/appdata}"
  MEDIA_DIR="${MEDIA_DIR:-$STORAGE_ROOT/media}"
  TRANSCODE_DIR="${TRANSCODE_DIR:-/srv/appdata/plex/transcode}"
  PUID="${PUID:-1000}"
  PGID="${PGID:-1000}"
  TZ="${TZ:-America/Sao_Paulo}"
  PLEX_CLAIM="${PLEX_CLAIM:-}"
  PLEX_ADVERTISE_IP="${PLEX_ADVERTISE_IP:-}"
  INSTALL_AI="${INSTALL_AI:-0}"
  OLLAMA_MODELS_DIR="${OLLAMA_MODELS_DIR:-/srv/appdata/ollama}"
  FAMILY_USER="${FAMILY_USER:-familia}"
}

dnf_install() {
  dnf install -y "$@"
}

enable_now() {
  systemctl enable --now "$@"
}

write_file() {
  local path="$1"
  install -d -m 0755 "$(dirname "$path")"
  cat > "$path"
}
