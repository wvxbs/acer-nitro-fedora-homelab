# OneDrive Media Server

Use Jellyfin plus `rclone mount` as the default media stack. Jellyfin is local-first and does not require a Plex account. Rclone presents OneDrive as a read-only filesystem and only downloads movie data when a client actually reads it.

## Recommendation

Prefer this path:

```text
OneDrive -> rclone mount -> /srv/storage/media/onedrive -> Jellyfin -> TV/browser/app
```

This avoids filling the 256 GB SSD. The SSD only stores Jellyfin metadata and a bounded rclone VFS cache.

Plex can still be run, but Jellyfin is the lower-friction local option for this homelab.

## Shared Link Caveat

A public `1drv.ms` folder link is not enough for a stable media library mount. Media servers need directory listing, random reads, seeking and reconnects. Configure an authenticated OneDrive remote with `rclone config`. If the folder is shared from another account, first add it to your OneDrive or copy/shortcut it so it appears under the authenticated remote.

Given link for reference:

```text
https://1drv.ms/f/c/dca378c12445f4d0/IgDQ9EUkwXijIIDcJl8AAAAAAd18A9mGT-1GBkgtZVp5XPw?e=8s4Qgo
```

## Paths

```text
Remote path:          onedrive:Vídeos/Filmes
Host mountpoint:      /srv/storage/media/onedrive
Jellyfin media path:  /media/onedrive
VFS cache directory:  /srv/appdata/rclone/vfs-cache
Jellyfin URL:         https://jellyfin.nitro.lan
```

Adjust `ONEDRIVE_PATH` if your actual folder path differs.

## Configure Rclone

Run as the Fedora user:

```bash
rclone config
rclone lsd onedrive:
rclone lsf onedrive:Vídeos/Filmes
```

Then start the Docker media profile:

```bash
cd /opt/homelab
docker compose --profile media up -d rclone-jellyfin jellyfin
```

Legacy systemd mount, only if you intentionally choose not to use Docker for the
mount:

```bash
sudo systemctl enable --now rclone-onedrive-mount.service
systemctl status rclone-onedrive-mount.service
ls -la /srv/storage/media/onedrive
```

## Start Jellyfin

```bash
cd /opt/homelab
docker compose --profile media up -d jellyfin
```

Open:

```text
http://jellyfin.nitro.lan
```

Add a library with folder:

```text
/media/onedrive
```

Only the configured OneDrive folder is mounted. For this homelab that is the
`Vídeos/Filmes` folder inside the authenticated OneDrive account.

```text
OneDrive/Vídeos/Filmes
```

## Cache Behavior

Jellyfin reads media through the rclone FUSE mount. Rclone then requests the
needed ranges from OneDrive as the player reads and seeks through the file. The
library is not fully downloaded to the SSD.

The mount is read-only, so Jellyfin cannot upload changes back to OneDrive. The
SSD stores only Jellyfin metadata plus a bounded rclone VFS cache. With
`vfs-cache-mode full`, rclone may cache a file or chunks while playback is
active so seeking works correctly.

The cache is not guaranteed to disappear the instant playback stops. It is
removed by policy when files are no longer in use, when they age out, when the
cache reaches the configured size, or when free disk space drops below the
minimum. Current logs have shown rclone removing movie cache files after use and
when the cache policy requested space back.

## Cache Defaults

```text
RCLONE_VFS_CACHE_MAX_SIZE=40G
RCLONE_VFS_CACHE_MAX_AGE=12h
RCLONE_VFS_CACHE_MIN_FREE_SPACE=30G
RCLONE_BUFFER_SIZE=64M
```

These defaults favor not filling the SSD. Increase max cache only after checking free space.

## Subtitles

Put subtitle files next to the movie file in the same OneDrive folder. Use the
same base filename as the movie:

```text
Enter the Void.mkv
Enter the Void.pt-BR.srt
Enter the Void.en.srt
```

For this setup, sidecar subtitle files in OneDrive are the safest source of
truth because the media mount is read-only and survives container recreation.

## Health Checks

```bash
docker logs rclone-jellyfin --tail 100
du -sh /srv/appdata/rclone/vfs-cache
```

If Jellyfin was already running before the mount came up, restart it:

```bash
docker restart jellyfin
```
