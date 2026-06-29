# Current Homelab State

This file records the intended reproducible state of the Nitro homelab.

## Host

```text
Hostname: nitro-homelab
Primary service IP: 192.168.15.8
Wired interface: enp7s0, static 192.168.15.8/24, default route metric 100
Wi-Fi fallback: wlp8s0, DHCP, default route metric 600
OS: Fedora Server
GPU: NVIDIA GTX 1650, 4 GB VRAM
Root LV: /dev/fedora/root expanded to 180 GB
```

The service IP `192.168.15.8/24` should stay on the wired NetworkManager
connection. Wi-Fi can exist as a fallback route, but Ethernet must keep the
lower route metric whenever the cable is available. Reapply this with:

```bash
sudo ./scripts/55-network-failover.sh
```

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
<<<<<<< HEAD
Glances        https://glances.nitro.lan
Nitro Telemetry https://performance.nitro.lan (gpu.nitro.lan is an alias)
File Drop      \\192.168.15.8\drop or smb://192.168.15.8/drop
Host Terminal  http://terminal.nitro.lan, optional emergency browser shell
=======
Performance    https://performance.nitro.lan
Security       https://security.nitro.lan
Processes      https://processes.nitro.lan
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
```

Ollama and Open WebUI are part of the AI profile. The dashboard keeps optional links visible and marks their healthcheck offline when a profile is stopped.
Host Terminal is part of the explicit `terminal` profile and should be stopped
when not needed.

The checked-in compose bundle also preserves the latest standalone operational
helpers from `/opt/homelab`: `compose/performance/server.py`,
`compose/security/server.py`, and `compose/codex-runner/Dockerfile`. The active
Compose file uses `compose/performance/server.py` for the consolidated
`performance.nitro.lan` telemetry page.

## Power and Network Policy

```text
CPU governor: powersave where writable
CPU energy preference: balance_power where writable
NVIDIA runtime D3: enabled through /etc/modprobe.d/nvidia-power-management.conf
Ethernet route metric: preferred over Wi-Fi
Wi-Fi route metric: fallback
```

Reapply the host policy with:

```bash
sudo ./scripts/35-power-tuning.sh
sudo ./scripts/55-network-failover.sh
```

## File Drop

```text
Protocol: SMB2/SMB3, guest access
LAN path: \\192.168.15.8\drop
Server path: /srv/storage/drop
Retention: 24 hours by default
Target size: 100G by default
Authentication: guest-only by default; optional local SMB username/password for clients that block guest
Discovery: WSD advertisement as nitro-drop plus Bonjour/Avahi SMB service when multicast works
```

This is intentionally temporary and low-friction. Guest access is the default;
optional SMB credentials belong only in the local `.env`, never in Git. See
`docs/FILE_DROP.md`.

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
<<<<<<< HEAD
OpenClaw     https://openclaw.nitro.lan
Models       llama3.2:3b, qwen2.5-coder:1.5b
Codex CLI    installed per Linux user during that user's setup/login, not shared globally
=======
Models       nitro-coder, nitro-chat, llama3.2:3b, qwen2.5-coder:1.5b
Codex CLI    available through the codex-wvxbs container and optional per-user SSH installs
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
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

## Host Terminal

```text
URL: http://terminal.nitro.lan
Profile: terminal
Bind: 127.0.0.1:7681 behind Caddy
Authentication: TERMINAL_AUTH_MODE=proxy with Caddy basic auth
Credential material: TERMINAL_USERNAME / TERMINAL_PASSWORD_HASH in local .env only
Direct ttyd mode: TERMINAL_AUTH_MODE=basic, not recommended
Experimental mode: TERMINAL_AUTH_MODE=system with Fedora host login prompt
Runtime: privileged container, required for host namespace entry on Fedora
Access level: host shell through nsenter after login
```

Use it only as an emergency browser fallback for host administration. See
`docs/HOST_TERMINAL.md`.

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
