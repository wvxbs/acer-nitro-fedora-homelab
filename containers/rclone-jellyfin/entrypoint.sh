#!/usr/bin/env sh
set -eu

: "${RCLONE_REMOTE_NAME:=onedrive}"
: "${ONEDRIVE_PATH:?Set ONEDRIVE_PATH to the remote media folder, for example Videos/Movies.}"
: "${RCLONE_MOUNT_PATH:=/media/onedrive}"
: "${RCLONE_CONFIG:=/config/rclone.conf}"
: "${RCLONE_CACHE_DIR:=/cache}"
: "${RCLONE_VFS_CACHE_MAX_SIZE:=40G}"
: "${RCLONE_VFS_CACHE_MAX_AGE:=12h}"
: "${RCLONE_VFS_CACHE_MIN_FREE_SPACE:=30G}"
: "${RCLONE_BUFFER_SIZE:=64M}"
: "${RCLONE_LOG_LEVEL:=INFO}"

if [ ! -r "$RCLONE_CONFIG" ]; then
  echo "rclone config not readable: $RCLONE_CONFIG" >&2
  exit 2
fi

mkdir -p "$RCLONE_MOUNT_PATH" "$RCLONE_CACHE_DIR"

exec rclone mount "${RCLONE_REMOTE_NAME}:${ONEDRIVE_PATH}" "$RCLONE_MOUNT_PATH" \
  --config "$RCLONE_CONFIG" \
  --read-only \
  --allow-other \
  --allow-non-empty \
  --dir-cache-time 12h \
  --poll-interval 1m \
  --vfs-cache-mode full \
  --vfs-cache-max-size "$RCLONE_VFS_CACHE_MAX_SIZE" \
  --vfs-cache-max-age "$RCLONE_VFS_CACHE_MAX_AGE" \
  --vfs-cache-min-free-space "$RCLONE_VFS_CACHE_MIN_FREE_SPACE" \
  --vfs-read-chunk-size 64M \
  --vfs-read-chunk-size-limit 1G \
  --buffer-size "$RCLONE_BUFFER_SIZE" \
  --cache-dir "$RCLONE_CACHE_DIR" \
  --transfers 2 \
  --checkers 4 \
  --log-level "$RCLONE_LOG_LEVEL" \
  ${RCLONE_EXTRA_ARGS:-}
