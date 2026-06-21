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
    set -a
    # shellcheck disable=SC1090
    source "$config"
    set +a
  else
    warn "Config file not found: $config. Using defaults from scripts."
  fi

  HOMELAB_HOSTNAME="${HOMELAB_HOSTNAME:-nitro-pve}"
  ADMIN_USER="${ADMIN_USER:-root}"
  SSH_AUTHORIZED_KEYS="${SSH_AUTHORIZED_KEYS:-}"
  TZ="${TZ:-America/Sao_Paulo}"

  PROXMOX_BRIDGE="${PROXMOX_BRIDGE:-vmbr0}"
  MEDIA_CT_ID="${MEDIA_CT_ID:-120}"
  MEDIA_CT_HOSTNAME="${MEDIA_CT_HOSTNAME:-media}"
  MEDIA_CT_MEMORY="${MEDIA_CT_MEMORY:-4096}"
  MEDIA_CT_SWAP="${MEDIA_CT_SWAP:-512}"
  MEDIA_CT_CORES="${MEDIA_CT_CORES:-2}"
  MEDIA_CT_ROOTFS="${MEDIA_CT_ROOTFS:-local-lvm:24}"
  MEDIA_CT_STORAGE="${MEDIA_CT_STORAGE:-local}"
  MEDIA_CT_UNPRIVILEGED="${MEDIA_CT_UNPRIVILEGED:-0}"
  MEDIA_CT_PASSWORD="${MEDIA_CT_PASSWORD:-}"
  MEDIA_CT_IP="${MEDIA_CT_IP:-dhcp}"
  DEBIAN_CT_RELEASE="${DEBIAN_CT_RELEASE:-12}"

  INSTALL_NVIDIA="${INSTALL_NVIDIA:-1}"
  ENABLE_NVIDIA_LXC="${ENABLE_NVIDIA_LXC:-1}"

  INSTALL_TAILSCALE="${INSTALL_TAILSCALE:-1}"
  TAILSCALE_AUTHKEY="${TAILSCALE_AUTHKEY:-}"
  TAILSCALE_EXTRA_ARGS="${TAILSCALE_EXTRA_ARGS:---ssh}"

  EXTERNAL_DISK_UUID="${EXTERNAL_DISK_UUID:-}"
  EXTERNAL_DISK_FSTYPE="${EXTERNAL_DISK_FSTYPE:-ext4}"
  EXTERNAL_MOUNTPOINT="${EXTERNAL_MOUNTPOINT:-/srv/storage}"

  APPDATA_DIR="${APPDATA_DIR:-/srv/appdata}"
  MEDIA_DIR="${MEDIA_DIR:-/srv/storage/media}"
  TRANSCODE_DIR="${TRANSCODE_DIR:-/srv/appdata/plex/transcode}"
  ONEDRIVE_LOCAL_PATH="${ONEDRIVE_LOCAL_PATH:-/srv/storage/incoming/onedrive}"

  RCLONE_REMOTE_NAME="${RCLONE_REMOTE_NAME:-onedrive}"
  ONEDRIVE_PATH="${ONEDRIVE_PATH:-Rips/DVD}"
  RCLONE_USER="${RCLONE_USER:-plex}"
  RCLONE_SCHEDULE="${RCLONE_SCHEDULE:-*:0/30}"
  RCLONE_BWLIMIT="${RCLONE_BWLIMIT:-}"

  INSTALL_PLEX="${INSTALL_PLEX:-1}"
  PLEX_CLAIM="${PLEX_CLAIM:-}"

  INSTALL_COMPOSE_BUNDLE="${INSTALL_COMPOSE_BUNDLE:-0}"
  HOMELAB_ROOT="${HOMELAB_ROOT:-/opt/homelab}"
  PUID="${PUID:-1000}"
  PGID="${PGID:-1000}"
  PLEX_ADVERTISE_IP="${PLEX_ADVERTISE_IP:-}"
  INSTALL_AI="${INSTALL_AI:-0}"
  OLLAMA_MODELS_DIR="${OLLAMA_MODELS_DIR:-/srv/appdata/ollama}"
}

apt_install() {
  DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"
}

enable_now() {
  systemctl enable --now "$@"
}

is_proxmox() {
  [[ -d /etc/pve ]] && command -v pveversion >/dev/null 2>&1
}

require_proxmox() {
  if ! is_proxmox; then
    die "This bootstrap targets a Proxmox VE host. Install Proxmox first."
  fi
}

pct_exists() {
  pct status "$1" >/dev/null 2>&1
}

pct_is_running() {
  pct status "$1" 2>/dev/null | grep -q 'status: running'
}

pct_exec() {
  pct exec "$MEDIA_CT_ID" -- "$@"
}
