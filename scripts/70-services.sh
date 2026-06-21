#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config
require_proxmox

log "Creating/configuring media LXC"

mapfile -t templates < <(pveam list "$MEDIA_CT_STORAGE" | awk -v rel="debian-${DEBIAN_CT_RELEASE}-standard" '$1 ~ rel && $1 ~ /amd64/ {print $1}' | sort -V)
if [[ "${#templates[@]}" -eq 0 ]]; then
  die "No downloaded Debian ${DEBIAN_CT_RELEASE} template found on $MEDIA_CT_STORAGE. Run scripts/20-lxc-template.sh first."
fi
template="${templates[-1]}"

if ! pct_exists "$MEDIA_CT_ID"; then
  create_args=(
    "$MEDIA_CT_ID" "$template"
    --hostname "$MEDIA_CT_HOSTNAME"
    --cores "$MEDIA_CT_CORES"
    --memory "$MEDIA_CT_MEMORY"
    --swap "$MEDIA_CT_SWAP"
    --rootfs "$MEDIA_CT_ROOTFS"
    --net0 "name=eth0,bridge=$PROXMOX_BRIDGE,ip=$MEDIA_CT_IP"
    --unprivileged "$MEDIA_CT_UNPRIVILEGED"
    --features nesting=1,keyctl=1
    --ostype debian
    --start 0
  )
  if [[ -n "$MEDIA_CT_PASSWORD" ]]; then
    create_args+=(--password "$MEDIA_CT_PASSWORD")
  fi
  pct create "${create_args[@]}"
else
  log "CT $MEDIA_CT_ID already exists. Reusing it."
fi

pct set "$MEDIA_CT_ID" -mp0 "$APPDATA_DIR",mp=/srv/appdata,backup=0
pct set "$MEDIA_CT_ID" -mp1 "$MEDIA_DIR",mp=/media,backup=0
pct set "$MEDIA_CT_ID" -mp2 "$TRANSCODE_DIR",mp=/transcode,backup=0
pct set "$MEDIA_CT_ID" -mp3 "$ONEDRIVE_LOCAL_PATH",mp=/incoming/onedrive,backup=0

conf="/etc/pve/lxc/${MEDIA_CT_ID}.conf"
if [[ "$ENABLE_NVIDIA_LXC" == "1" ]]; then
  grep -q 'homelab-nvidia-begin' "$conf" 2>/dev/null || cat >> "$conf" <<'EOF'
# homelab-nvidia-begin
lxc.cgroup2.devices.allow: c 195:* rwm
lxc.cgroup2.devices.allow: c 226:* rwm
lxc.cgroup2.devices.allow: c 234:* rwm
lxc.mount.entry: /dev/nvidia0 dev/nvidia0 none bind,optional,create=file
lxc.mount.entry: /dev/nvidiactl dev/nvidiactl none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-modeset dev/nvidia-modeset none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm dev/nvidia-uvm none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm-tools dev/nvidia-uvm-tools none bind,optional,create=file
lxc.mount.entry: /dev/dri dev/dri none bind,optional,create=dir
# homelab-nvidia-end
EOF
fi

pct start "$MEDIA_CT_ID" || true
sleep 5

ct_codename="$(pct_exec bash -lc '. /etc/os-release && printf %s "$VERSION_CODENAME"')"
pct_exec bash -lc "cat > /etc/apt/sources.list.d/debian-nonfree.sources" <<EOF
Types: deb
URIs: http://deb.debian.org/debian
Suites: $ct_codename ${ct_codename}-updates
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: http://security.debian.org/debian-security
Suites: ${ct_codename}-security
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
EOF

pct_exec apt-get update
pct_exec env DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl gnupg rclone vainfo nvidia-smi libnvidia-encode1 libnvidia-decode1

if [[ "$INSTALL_PLEX" == "1" ]]; then
  pct_exec install -d -m 0755 /usr/share/keyrings
  pct_exec bash -lc 'curl -fsSL https://downloads.plex.tv/plex-keys/PlexSign.key | gpg --dearmor -o /usr/share/keyrings/plex.gpg'
  pct_exec bash -lc 'echo "deb [signed-by=/usr/share/keyrings/plex.gpg] https://downloads.plex.tv/repo/deb public main" > /etc/apt/sources.list.d/plexmediaserver.list'
  pct_exec apt-get update
  pct_exec env DEBIAN_FRONTEND=noninteractive apt-get install -y plexmediaserver
  pct_exec systemctl enable --now plexmediaserver
fi

pct_exec install -d -m 0755 /srv/appdata /media /transcode /incoming/onedrive
pct_exec chown -R plex:plex /srv/appdata /media /transcode /incoming/onedrive || true

log "Media CT ready. Plex should be available at http://<ct-ip>:32400/web"
pct exec "$MEDIA_CT_ID" -- hostname -I || true
