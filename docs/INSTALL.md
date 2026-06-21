# Install Guide

## Base: Proxmox VE

Use Proxmox VE on the internal SSD. During install:

- Prefer Ethernet.
- Use the SSD internal as the Proxmox system disk.
- Keep the external 5400 rpm disk for media, not VM storage.
- Disable Secure Boot in firmware for the lowest-friction NVIDIA path.
- Create a strong root password and keep the web UI on LAN/Tailscale only.

After first boot:

```bash
apt update
apt install -y git
git clone https://github.com/wvxbs/acer-nitro-fedora-homelab.git
cd acer-nitro-fedora-homelab
cp config/homelab.env.example config/homelab.env
nano config/homelab.env
./scripts/bootstrap.sh
reboot
./scripts/healthcheck.sh
```

## Config Values You Probably Want

```bash
HOMELAB_HOSTNAME=nitro-pve
PROXMOX_BRIDGE=vmbr0
MEDIA_CT_ID=120
MEDIA_CT_HOSTNAME=media
MEDIA_CT_MEMORY=4096
MEDIA_CT_CORES=2
EXTERNAL_DISK_UUID=uuid-do-hd-externo
RCLONE_REMOTE_NAME=onedrive
ONEDRIVE_PATH=Rips/DVD
```

Find the disk UUID on the Proxmox host:

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS
```

## What the Bootstrap Does

1. Updates the Proxmox host and installs basic tools.
2. Keeps the laptop awake with the lid closed.
3. Mounts the external disk if `EXTERNAL_DISK_UUID` is set.
4. Installs Tailscale on the host.
5. Installs the NVIDIA driver on the host.
6. Downloads a Debian LXC template.
7. Creates CT `media`.
8. Bind-mounts media/appdata/transcode paths into the CT.
9. Exposes `/dev/nvidia*` and `/dev/dri` to the CT.
10. Installs Plex and rclone inside the CT.

## Rclone

Configure OneDrive inside the media CT:

```bash
pct enter 120
su - plex
rclone config
rclone lsd onedrive:
exit
systemctl enable --now rclone-onedrive-pull.timer
```

Manual one-shot run:

```bash
pct exec 120 -- systemctl start rclone-onedrive-pull.service
pct exec 120 -- journalctl -u rclone-onedrive-pull.service -n 100 --no-pager
pct exec 120 -- tail -f /var/log/rclone/onedrive-pull.log
```

## Plex

Plex runs inside CT `media`:

- Web UI: `http://IP_DO_CT:32400/web`
- Media path inside Plex: `/media`
- Transcode path inside Plex: `/transcode`
- Incoming OneDrive path: `/incoming/onedrive`
