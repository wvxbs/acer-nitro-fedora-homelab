# rclone-jellyfin Docker Image

This repo builds a small rclone sidecar image for Jellyfin:

```text
wvxbs/rclone-jellyfin
```

The image does not contain OneDrive credentials, folder names, tokens, or any
private data. It only contains rclone, FUSE, and an entrypoint that mounts one
configured remote folder.

## What It Does

The container mounts:

```text
${RCLONE_REMOTE_NAME}:${ONEDRIVE_PATH}
```

into:

```text
/media/onedrive
```

The Compose file maps that mount back to the host:

```text
/srv/storage/media/onedrive
```

Jellyfin then reads it as:

```text
/media/onedrive
```

## Runtime Variables

These go in `/opt/homelab/.env` on the Nitro, not in Git:

```env
RCLONE_JELLYFIN_IMAGE=wvxbs/rclone-jellyfin:latest
RCLONE_REMOTE_NAME=onedrive
ONEDRIVE_PATH=Vídeos/Filmes
RCLONE_CONFIG_PATH=/home/<linux-user>/.config/rclone/rclone.conf
ONEDRIVE_MOUNT_PATH=/srv/storage/media/onedrive
RCLONE_CACHE_DIR=/srv/appdata/rclone/vfs-cache
RCLONE_VFS_CACHE_MAX_SIZE=40G
RCLONE_VFS_CACHE_MAX_AGE=12h
RCLONE_VFS_CACHE_MIN_FREE_SPACE=30G
RCLONE_BUFFER_SIZE=64M
```

`RCLONE_CONFIG_PATH` points to a local file that contains tokens. Never commit
that file.

## GitHub Actions Publish

The workflow is:

```text
.github/workflows/publish-rclone-jellyfin.yml
```

Create these repository secrets in GitHub:

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
```

`DOCKERHUB_TOKEN` should be a Docker Hub access token with permission to push
to `wvxbs/rclone-jellyfin`.

The workflow publishes:

```text
wvxbs/rclone-jellyfin:latest
wvxbs/rclone-jellyfin:<git-sha>
```

## Local Test Build

```bash
docker build -t wvxbs/rclone-jellyfin:local containers/rclone-jellyfin
```

## Start On The Nitro

```bash
cd /opt/homelab
docker compose --profile media up -d rclone-jellyfin jellyfin
docker logs -f rclone-jellyfin
```

Validate:

```bash
findmnt /srv/storage/media/onedrive
ls -la /srv/storage/media/onedrive
docker exec jellyfin ls -la /media/onedrive
```

## Security Notes

- The image is generic and public.
- The rclone config is private and mounted at runtime.
- The OneDrive mount is read-only.
- The VFS cache is bounded to avoid filling the SSD.
- Do not publish `.env`, `rclone.conf`, Docker logs with tokens, or browser auth
  exports.
