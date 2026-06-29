# Minecraft Servers

This homelab runs separate Minecraft Java and Bedrock servers from Docker.

```text
Java:    tcp/25565 -> minecraft-java
Bedrock: udp/19132 -> minecraft-bedrock
Data:    /srv/appdata/minecraft-java
         /srv/appdata/minecraft-bedrock
Backup:  onedrive:Documentos/Roms/Minecraft Worlds/Java
         onedrive:Documentos/Roms/Minecraft Worlds/Bedrock
```

The active worlds stay on the Nitro SSD for performance. OneDrive is only the
backup target. Do not run the live server world directly from an rclone mount.

## Configure

Edit the local env file before starting:

```bash
sudo nano /opt/homelab/.env
```

Useful knobs:

```env
MINECRAFT_BIND_IP=0.0.0.0
MINECRAFT_JAVA_PORT=25565
MINECRAFT_BEDROCK_PORT=19132
MINECRAFT_JAVA_MEMORY=6G
MINECRAFT_JAVA_ENABLE_WHITELIST=false
MINECRAFT_JAVA_WHITELIST=
MINECRAFT_JAVA_OPS=
MINECRAFT_JAVA_ENABLE_RCON=false
MINECRAFT_JAVA_RCON_PASSWORD=
```

Leave RCON disabled unless you need remote console automation. If you enable it,
set a unique local `MINECRAFT_JAVA_RCON_PASSWORD` and keep it out of Git.

## Start

```bash
cd /opt/homelab
docker compose --profile games up -d minecraft-java minecraft-bedrock
```

## LAN Connect

Use the Nitro LAN IP.

```text
Java:    <nitro-ip>:25565
Bedrock: <nitro-ip>:19132
```

## Backups

The timer stops both servers briefly, archives the world directories, restarts
the servers, then uploads `.tar.zst` archives to OneDrive.

```bash
systemctl status nitro-minecraft-backup.timer
sudo systemctl start nitro-minecraft-backup.service
journalctl -u nitro-minecraft-backup.service -n 100
```

Default schedule:

```text
03:30 daily, plus up to 10 minutes randomized delay
```

## Performance

Java uses Paper plus Aikar JVM flags and defaults to 6 GB heap. Bedrock is the
official dedicated server in a container. GPU acceleration is not used because
Minecraft servers do not render frames; CPU single-thread performance, RAM, SSD
latency, and sane view/simulation distance matter most.
