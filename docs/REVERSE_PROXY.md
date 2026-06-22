# Reverse Proxy

Caddy exposes friendly LAN names for homelab services. The proxy redirects local
HTTP names to HTTPS and uses an internal Caddy certificate authority for LAN TLS.

## Start

```bash
cd /opt/homelab
docker compose --profile proxy up -d
```

## Local URLs

```text
https://nitro.lan             dashboard with links and healthchecks
https://adguard.nitro.lan
https://cockpit.nitro.lan
https://telemetry.nitro.lan
https://jellyfin.nitro.lan
https://openwebui.nitro.lan
https://ollama.nitro.lan
https://portainer.nitro.lan
https://dozzle.nitro.lan
https://performance.nitro.lan
https://security.nitro.lan
https://rcfeventos.nitro.lan
https://processes.nitro.lan
```

The base dashboard is intentionally simple and mobile-friendly. It is served by
Caddy from `compose/dashboard/index.html`.

## Local Certificate Authority

Browsers will show a certificate warning until the local Caddy root certificate
is trusted on each client device. Download it from the LAN:

```text
http://nitro.lan/ca/root.crt
https://nitro.lan/ca/root.crt
```

Install `root.crt` as a trusted root certificate on Windows, Android, iOS and
macOS devices that should access `https://*.nitro.lan` without warnings. This is
only for the private LAN names; it is not a public internet certificate.

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
openwebui.nitro.lan    -> 192.168.15.8
ollama.nitro.lan       -> 192.168.15.8
portainer.nitro.lan    -> 192.168.15.8
dozzle.nitro.lan       -> 192.168.15.8
performance.nitro.lan  -> 192.168.15.8
security.nitro.lan     -> 192.168.15.8
rcfeventos.nitro.lan   -> 192.168.15.8
processes.nitro.lan    -> 192.168.15.8
```

## Validation

```bash
curl -k -I https://nitro.lan/
curl -k -I https://nitro.lan/health/jellyfin
curl -k -I https://nitro.lan/health/adguard
curl -k -I https://performance.nitro.lan/
curl -k -I https://security.nitro.lan/
curl -k -I https://processes.nitro.lan/
curl -k -I https://nitro.lan/health/performance
curl -k -I https://nitro.lan/health/security
curl -k -I https://nitro.lan/health/processes
```
