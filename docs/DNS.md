# DNS Blocking

Use AdGuard Home for DNS filtering. It is lighter operationally than making the server a router/DHCP server, and the UI makes allowlisting easy when a site breaks.

## Current Policy

Applied on 2026-06-28:

- AdGuard Home stays DNS-only. DHCP remains on the router.
- DNS listens on the Nitro service IP, `192.168.15.8:53`.
- Global protection and malware/phishing safe browsing are enabled.
- Safe Search and parental controls remain disabled to avoid unnecessary breakage.
- Cache is tuned for performance: 64 MiB cache, minimum TTL 60 seconds, maximum TTL 1 day, optimistic cache enabled.
- Upstreams are plain DNS for latency and reliability: Quad9 malware-filtering DNS plus Cloudflare malware-filtering DNS.
- The `dvg` LAN (`192.168.15.0/24`) is explicitly protected.
- The DVG gateway (`192.168.15.1`) is explicitly protected in case the router proxies DNS.
- The `loft` LAN (`192.168.0.0/24`) is explicitly protected.
- The Archer WAN address (`192.168.15.5`) is explicitly protected because DNS from `loft` may appear to AdGuard as the router instead of individual `192.168.0.x` clients.

Enabled blocklists:

```text
AdGuard DNS filter
OISD Blocklist Big
HaGeZi's Pro Blocklist
AdGuard DNS Popup Hosts filter
```

This is intentionally less conservative than the original setup, but avoids stacking too many overlapping specialty lists so DNS performance stays sane.

## Safety Model

Keep these guardrails:

- Do not enable DHCP in AdGuard Home while router DHCP is still enabled.
- Use the router/ISP DNS as the rollback path.
- Add allowlist rules for specific broken domains instead of disabling protection.

## Start

After the bootstrap installs the Compose bundle:

```bash
cd /opt/homelab
docker compose --profile dns up -d
```

Open:

```text
http://192.168.15.8:3001
```

The current upstreams are already configured in AdGuard Home.

## Test Before Router Changes

From another machine:

```bash
nslookup example.com 192.168.15.8
nslookup doubleclick.net 192.168.15.8
```

Then manually set one phone or laptop to use `192.168.15.8` as DNS before changing router DHCP DNS.

## Router Rollout

Set router DHCP DNS on both networks to AdGuard:

```text
Primary DNS: 192.168.15.8
Secondary DNS: 9.9.9.9
```

This keeps the network usable if the Nitro is shut down or rebooting. Most
clients will use AdGuard while it is online; during an outage, clients can fall
back to Quad9 instead of losing DNS entirely. The tradeoff is that some clients
may occasionally use the secondary resolver and bypass ad blocking.

Do not make AdGuard Home the DHCP server unless you intentionally want to replace the router DHCP.

## DHCP Model

A single DHCP server for both `dvg` and `loft` is only safe if one of these is true:

- The Archer is put into AP/bridge mode, so `loft` devices join the same `192.168.15.0/24` LAN.
- The Archer supports DHCP relay from `192.168.0.0/24` to a DHCP server on `192.168.15.8`.

Do not run AdGuard DHCP while the Vivo/DVG router or Archer DHCP servers are
still active on the same broadcast network. Two DHCP servers on one LAN can hand
out conflicting gateways/DNS and create intermittent failures that are painful
for non-technical users.

Recommended transparent setup for now:

```text
DVG router: DHCP on, primary DNS = 192.168.15.8, secondary DNS = 9.9.9.9
Archer/Loft router: DHCP on, primary DNS = 192.168.15.8, secondary DNS = 9.9.9.9
AdGuard Home DHCP: off
```

Also check IPv6 on both routers. If IPv6 Router Advertisement/RDNSS advertises
the router or ISP as DNS, some clients may bypass AdGuard even when IPv4 DHCP
DNS is correct. Either disable IPv6 DNS advertisement, disable IPv6 on the LAN,
or configure the router to advertise an AdGuard-controlled DNS resolver.

Current intended layout:

```text
Office/Vivo LAN: 192.168.15.0/24
Nitro service IP: 192.168.15.8
Home/Loft router WAN: 192.168.15.5
Home/Loft LAN: 192.168.0.0/24
Router DHCP DNS on DVG: 192.168.15.8 primary, 9.9.9.9 secondary
Router DHCP DNS on Loft: 192.168.15.8 primary, 9.9.9.9 secondary
```

AdGuard has a dedicated protected client for `192.168.15.5` named
`Archer Loft Gateway`. Keep this exact client enabled; otherwise the Archer may
be harder to identify in the query log.

AdGuard also has a dedicated protected client for `192.168.15.1` named
`DVG Gateway`, useful when DVG clients or the router itself proxy DNS.

The Nitro keeps `192.168.15.8/24` on the wired connection so DNS continues to
work even if Wi-Fi changes. Keep AdGuard bound to `192.168.15.8:53`.

From the Nitro on `dvg`, the Archer management portal did not respond at either
`http://192.168.0.1`, `https://192.168.0.1`, `http://192.168.15.5`, or
`https://192.168.15.5`. Connect to the `loft` Wi-Fi/LAN to change the Archer
DHCP DNS at `http://192.168.0.1`.

## Local Names

Create these DNS rewrites in AdGuard Home, all pointing to `192.168.15.8`:

```text
nitro.lan
adguard.nitro.lan
cockpit.nitro.lan
telemetry.nitro.lan
jellyfin.nitro.lan
openwebui.nitro.lan
openclaw.nitro.lan
ollama.nitro.lan
portainer.nitro.lan
dozzle.nitro.lan
terminal.nitro.lan
filedrop.nitro.lan
```

## If Something Breaks

- Open the AdGuard Home query log.
- Find the blocked domain.
- Add an allowlist rule for that domain.
- If only one site/app breaks, allowlist the blocked domain.
- If either network loses DNS while the Nitro is running, change that router's DHCP DNS to `9.9.9.9` or `1.1.1.2` temporarily.
- If the Nitro is rebooting, wait for Docker to start; the `adguard-home` container uses `restart: unless-stopped`.
- If the Nitro is intentionally off, clients should fall back to `9.9.9.9`; ad blocking and `*.nitro.lan` names will be unavailable until the Nitro returns.
- To roll back the AdGuard config itself, restore `/srv/appdata/adguard/conf/AdGuardHome.yaml.bak.20260628-network-wide` to `/srv/appdata/adguard/conf/AdGuardHome.yaml` and restart the container.
