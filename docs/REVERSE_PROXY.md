# Reverse Proxy

Caddy exposes friendly LAN names for homelab services. The proxy listens on plain HTTP port `80`; TLS is intentionally disabled for local-only access.

## Start

```bash
cd /opt/homelab
docker compose --profile proxy up -d
```

## Local URLs

```text
http://nitro.lan
http://adguard.nitro.lan
http://cockpit.nitro.lan
http://telemetry.nitro.lan
http://jellyfin.nitro.lan
http://plex.nitro.lan
http://portainer.nitro.lan
http://dozzle.nitro.lan
```

## DNS Requirement

These names only work on clients that use AdGuard Home as DNS. Configure the router DHCP DNS, or the client DNS, to:

```text
192.168.15.8
```

If a client still uses the home router as DNS, for example `192.168.0.1`, it may return NXDOMAIN for `*.nitro.lan`. Test directly with:

```bash
nslookup telemetry.nitro.lan 192.168.15.8
```

## AdGuard Rewrites

Create DNS rewrites in AdGuard Home pointing each hostname to `192.168.15.8`.

```text
nitro.lan              -> 192.168.15.8
adguard.nitro.lan      -> 192.168.15.8
cockpit.nitro.lan      -> 192.168.15.8
telemetry.nitro.lan    -> 192.168.15.8
jellyfin.nitro.lan     -> 192.168.15.8
plex.nitro.lan         -> 192.168.15.8
portainer.nitro.lan    -> 192.168.15.8
dozzle.nitro.lan       -> 192.168.15.8
```

## Validation

```bash
curl -I -H 'Host: telemetry.nitro.lan' http://192.168.15.8/
```
