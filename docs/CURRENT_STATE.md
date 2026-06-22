# Current Homelab State

This file records the intended reproducible state of the Nitro homelab.

## Host

```text
Hostname: nitro-homelab
Primary service IP: 192.168.15.8
Secondary observed Ethernet IP: 192.168.15.6
OS: Fedora Server
GPU: NVIDIA GTX 1650, 4 GB VRAM
Root LV: /dev/fedora/root expanded to 180 GB
```

The service IP `192.168.15.8/24` should stay on the wired NetworkManager
connection. Wi-Fi can exist, but it should not become the default route for the
server if Ethernet is available.

## Core Services

```text
AdGuard Home   DNS on 192.168.15.8:53, UI on https://adguard.nitro.lan
Caddy          reverse proxy and dashboard on https://nitro.lan
Cockpit        https://cockpit.nitro.lan
Jellyfin       https://jellyfin.nitro.lan
Telemetry Lab  https://telemetry.nitro.lan
Ollama         https://ollama.nitro.lan
Open WebUI     https://openwebui.nitro.lan
Portainer      https://portainer.nitro.lan
Dozzle         https://dozzle.nitro.lan
Performance    https://performance.nitro.lan
Processes      https://processes.nitro.lan
```

Ollama and Open WebUI are part of the AI profile. The dashboard keeps optional links visible and marks their healthcheck offline when a profile is stopped.

## OneDrive Media

```text
Rclone remote: onedrive
Remote path: onedrive:Vídeos/Filmes
Mount path: /srv/storage/media/onedrive
Jellyfin path: /media/onedrive
Mount mode: read-only
VFS cache: /srv/appdata/rclone/vfs-cache
Mount container: wvxbs/rclone-jellyfin
Cache policy: bounded VFS cache, dynamic reads from OneDrive
```

## Local AI

```text
Ollama       https://ollama.nitro.lan
Open WebUI   https://openwebui.nitro.lan
Models       nitro-coder, nitro-chat, llama3.2:3b, qwen2.5-coder:1.5b
Codex CLI    available through the codex-wvxbs container and optional per-user SSH installs
```

Codex delegation can use either SSH remote projects with isolated Linux users or the `codex-wvxbs` container for the main admin account. See `docs/REMOTE_AI_DELEGATION.md`.

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
docker compose --profile ops up -d performance portainer dozzle
./scripts/healthcheck.sh
```
