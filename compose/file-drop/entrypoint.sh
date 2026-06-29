#!/usr/bin/env bash
set -euo pipefail

DROP_PATH="${DROP_PATH:-/drop}"
SHARE_NAME="${FILE_DROP_SHARE_NAME:-drop}"
WORKGROUP="${FILE_DROP_WORKGROUP:-WORKGROUP}"
NETBIOS_NAME="${FILE_DROP_NETBIOS_NAME:-NITRO-DROP}"
HOSTNAME_NAME="${FILE_DROP_HOSTNAME:-nitro-drop}"
PUID="${PUID:-1000}"
PGID="${PGID:-1000}"
GUEST_USER="${FILE_DROP_GUEST_USER:-filedrop}"
SMB_USER="${FILE_DROP_USERNAME:-}"
SMB_PASSWORD="${FILE_DROP_PASSWORD:-}"
MAX_SIZE="${FILE_DROP_MAX_SIZE:-100G}"
MAX_SIZE_MB="$(
  case "${MAX_SIZE: -1}" in
    K|k) awk -v n="${MAX_SIZE%?}" 'BEGIN { printf "%.0f", n / 1024 }' ;;
    M|m) awk -v n="${MAX_SIZE%?}" 'BEGIN { printf "%.0f", n }' ;;
    G|g) awk -v n="${MAX_SIZE%?}" 'BEGIN { printf "%.0f", n * 1024 }' ;;
    T|t) awk -v n="${MAX_SIZE%?}" 'BEGIN { printf "%.0f", n * 1024 * 1024 }' ;;
    *) awk -v n="$MAX_SIZE" 'BEGIN { printf "%.0f", n / 1024 / 1024 }' ;;
  esac
)"

if [[ "$#" -gt 0 ]]; then
  exec "$@"
fi

if ! getent group "$GUEST_USER" >/dev/null; then
  groupadd -g "$PGID" "$GUEST_USER"
fi

if ! id "$GUEST_USER" >/dev/null 2>&1; then
  useradd -M -u "$PUID" -g "$GUEST_USER" -s /usr/sbin/nologin "$GUEST_USER"
fi

install -d -m 0777 -o "$GUEST_USER" -g "$GUEST_USER" "$DROP_PATH"
install -d -m 0755 /run/samba /var/cache/samba /var/log/samba

if [[ -n "$SMB_USER" || -n "$SMB_PASSWORD" ]]; then
  if [[ -z "$SMB_USER" || -z "$SMB_PASSWORD" ]]; then
    printf '%s\n' "Set both FILE_DROP_USERNAME and FILE_DROP_PASSWORD, or leave both empty for guest-only SMB." >&2
    exit 64
  fi

  if [[ "$SMB_PASSWORD" == "$SMB_USER" || "$SMB_PASSWORD" =~ ^(drop|password|changeme|admin|guest)$ ]]; then
    printf '%s\n' "Refusing weak FILE_DROP_PASSWORD. Leave it empty for guest-only SMB or choose a unique LAN password." >&2
    exit 64
  fi

  if ! id "$SMB_USER" >/dev/null 2>&1; then
    useradd -M -g "$GUEST_USER" -s /usr/sbin/nologin "$SMB_USER"
  fi

  printf '%s\n%s\n' "$SMB_PASSWORD" "$SMB_PASSWORD" | smbpasswd -s -a "$SMB_USER" >/dev/null
fi

cat > /etc/samba/smb.conf <<EOF
[global]
   server string = Nitro File Drop
   workgroup = ${WORKGROUP}
   netbios name = ${NETBIOS_NAME}
   server role = standalone server
   map to guest = Bad User
   guest account = ${GUEST_USER}
   security = user
   disable spoolss = yes
   load printers = no
   printing = bsd
   log file = /dev/stdout
   log level = 1 auth:3
   max log size = 0
   smb ports = 445 139
   server min protocol = SMB2_02
   server max protocol = SMB3
   server signing = auto
   smb encrypt = off
   use sendfile = yes
   min receivefile size = 16384
   aio read size = 1
   aio write size = 1
   strict sync = no
   sync always = no
   getwd cache = yes
   max disk size = ${MAX_SIZE_MB}

[${SHARE_NAME}]
   path = ${DROP_PATH}
   comment = Temporary LAN file drop - guest access
   browseable = yes
   read only = no
   guest ok = yes
   guest only = no
   public = yes
   force user = ${GUEST_USER}
   force group = ${GUEST_USER}
   create mask = 0666
   force create mode = 0666
   directory mask = 0777
   force directory mode = 0777
   inherit permissions = yes
   ea support = yes
EOF

if command -v wsdd >/dev/null 2>&1; then
  wsdd --hostname "$HOSTNAME_NAME" --workgroup "$WORKGROUP" --shortlog &
fi

nmbd --foreground --no-process-group &
exec smbd --foreground --no-process-group
