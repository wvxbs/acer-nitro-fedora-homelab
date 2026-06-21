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
Remote path:          onedrive:Rips/DVD
Host mountpoint:      /srv/storage/media/onedrive
Jellyfin media path:  /media/onedrive
VFS cache directory:  /srv/appdata/rclone/vfs-cache
Jellyfin URL:         http://jellyfin.nitro.lan
```

Adjust `ONEDRIVE_PATH` if your actual folder path differs.

## Configure Rclone

Run as the Fedora user:

```bash
rclone config
rclone lsd onedrive:
rclone lsf onedrive:Rips/DVD
```

Then enable the mount:

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

## Cache Defaults

```text
RCLONE_VFS_CACHE_MAX_SIZE=40G
RCLONE_VFS_CACHE_MAX_AGE=12h
RCLONE_VFS_CACHE_MIN_FREE_SPACE=30G
RCLONE_BUFFER_SIZE=64M
```

These defaults favor not filling the SSD. Increase max cache only after checking free space.

## Health Checks

```bash
systemctl status rclone-onedrive-mount.service
journalctl -u rclone-onedrive-mount.service -n 100 --no-pager
tail -f /var/log/rclone/onedrive-mount.log
du -sh /srv/appdata/rclone/vfs-cache
```

If Jellyfin was already running before the mount came up, restart it:

```bash
docker restart jellyfin
```
