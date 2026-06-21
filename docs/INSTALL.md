# Install Guide

## Fedora Server

Use Fedora Server, not Workstation. During install:

- Enable OpenSSH if the installer offers it.
- Keep automatic partitioning unless you want a custom layout.
- Use Ethernet if available.
- Create your normal admin user.

After first boot:

```bash
sudo dnf install -y git
git clone https://github.com/SEU_USUARIO/acer-nitro-fedora-homelab.git
cd acer-nitro-fedora-homelab
cp config/homelab.env.example config/homelab.env
nano config/homelab.env
sudo ./scripts/bootstrap.sh
sudo reboot
./scripts/healthcheck.sh
```

## Config Values You Probably Want

```bash
HOMELAB_HOSTNAME=nitro-homelab
ADMIN_USER=seu_usuario_no_fedora
INSTALL_TAILSCALE=1
EXTERNAL_DISK_UUID=uuid-do-hd-externo
RCLONE_REMOTE_NAME=onedrive
ONEDRIVE_PATH=Rips/DVD
ONEDRIVE_LOCAL_PATH=/srv/storage/incoming/onedrive
MEDIA_DIR=/srv/storage/media
```

Find the disk UUID:

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS
```

## First Container Start

```bash
cd /opt/homelab
docker compose --profile media --profile ops up -d
```

Plex uses host networking:

- Web UI: `http://HOST:32400/web`
- Media path inside Plex: `/media`
- Transcode path inside Plex: `/transcode`

## Rclone

Configure OneDrive as the normal Fedora user:

```bash
rclone config
rclone lsd onedrive:
sudo systemctl enable --now rclone-onedrive-pull.timer
```

Manual one-shot run:

```bash
sudo systemctl start rclone-onedrive-pull.service
journalctl -u rclone-onedrive-pull.service -n 100 --no-pager
tail -f /var/log/rclone/onedrive-pull.log
```
