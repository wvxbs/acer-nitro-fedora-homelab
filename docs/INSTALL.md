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
STORAGE_ROOT=/srv/storage
RCLONE_REMOTE_NAME=onedrive
ONEDRIVE_PATH=Vídeos/Filmes
ONEDRIVE_MOUNT_PATH=/srv/storage/media/onedrive
MEDIA_DIR=/srv/storage/media
```

Inspect disks if you need to confirm the internal SSD layout:

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS
```

## LVM Root Size

Fedora may create a small 15 GB root logical volume even when the SSD has much more free LVM space. Docker images, Open WebUI and local models need more room. Check with:

```bash
df -h /
sudo vgs
sudo lvs
```

If the volume group has free space, grow root online:

```bash
sudo lvextend -r -L 180G /dev/fedora/root
```

This repo assumes the Nitro root LV has enough space for containers and caches.

## First Container Start

```bash
cd /opt/homelab
docker compose --profile media --profile ops up -d
```

Jellyfin uses host networking:

- Web UI: `https://jellyfin.nitro.lan`
- Media path inside Jellyfin: `/media/onedrive`

## Rclone Mount

Configure OneDrive as the normal Fedora user:

```bash
rclone config
rclone lsd onedrive:
```

Start the Docker mount and Jellyfin:

```bash
cd /opt/homelab
docker compose --profile media up -d rclone-jellyfin jellyfin
docker logs -f rclone-jellyfin
```
