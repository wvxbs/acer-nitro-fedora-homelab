# Current Homelab State

This file records the intended reproducible state of the Nitro homelab.

## Host

```text
Hostname: nitro-homelab
Primary service IP: 192.168.15.8
Secondary observed Ethernet IP: 192.168.15.6
OS: Fedora Server
GPU: NVIDIA GTX 1650, 4 GB VRAM
```

The service IP `192.168.15.8/24` should stay on the wired NetworkManager
connection. Wi-Fi can exist, but it should not become the default route for the
server if Ethernet is available.

## Core Services

```text
AdGuard Home   DNS on 192.168.15.8:53, UI on http://adguard.nitro.lan
Caddy          reverse proxy and dashboard on http://nitro.lan
Cockpit        http://cockpit.nitro.lan
Jellyfin       http://jellyfin.nitro.lan
Telemetry Lab  http://telemetry.nitro.lan
Ollama         http://ollama.nitro.lan
Open WebUI     http://openwebui.nitro.lan
Plex           http://plex.nitro.lan
Portainer      http://portainer.nitro.lan
Dozzle         http://dozzle.nitro.lan
```

Some optional services may be offline until their Compose profile is started.
The dashboard keeps the link visible and marks the healthcheck offline.

## OneDrive Media

```text
Rclone remote: onedrive
Remote path: onedrive:Vídeos/Filmes
Mount path: /srv/storage/media/onedrive
Jellyfin path: /media/onedrive
Mount mode: read-only
VFS cache: /srv/appdata/rclone/vfs-cache
Mount container: wvxbs/rclone-jellyfin
```

## Family Access

The optional limited OS user defaults to:

```text
FAMILY_USER=familia
```

It is not in `wheel` or `docker`. A polkit rule lets it reboot or power off
through Cockpit without broad sudo.

AdGuard Home does not provide true read-only roles. Create a separate AdGuard
login if family members need the dashboard, but understand that AdGuard accounts
can change AdGuard settings.

## Recreate Checklist

1. Install Fedora Server.
2. Clone this repo.
3. Copy `config/homelab.env.example` to `config/homelab.env`.
4. Fill `ADMIN_USER`, SSH keys, and optional Tailscale settings.
5. Run `sudo ./scripts/bootstrap.sh`.
6. Reboot after NVIDIA installation if the kernel/driver changed.
7. Configure rclone as the target user.
8. Enable the rclone mount.
9. Start required Compose profiles.
10. Configure AdGuard DNS rewrites and router DHCP DNS.

Useful commands:

```bash
cd /opt/homelab
docker compose --profile dns --profile proxy --profile media up -d
docker compose --profile ai up -d
./scripts/healthcheck.sh
```
