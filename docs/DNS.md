# DNS Blocking

Use AdGuard Home for DNS filtering. It is lighter operationally than making the server a router/DHCP server, and the UI makes allowlisting easy when a site breaks.

## Safety Model

Start in test mode:

- Do not enable DHCP in AdGuard Home.
- Do not point the whole router at it on day one.
- Use only AdGuard's default filter at first.
- Add extra lists slowly.
- Keep the router/ISP DNS as your rollback path.

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

Choose conservative upstream DNS servers, for example Cloudflare or Quad9. Avoid enabling family/safe-search modes until basic browsing is proven.

## Test Before Router Changes

From another machine:

```bash
nslookup example.com 192.168.15.8
nslookup doubleclick.net 192.168.15.8
```

Then manually set one phone or laptop to use `192.168.15.8` as DNS. Use it for a day before changing the router DHCP DNS.

## Router Rollout

Only after testing, set the router DHCP DNS server to:

```text
192.168.15.8
```

Do not make AdGuard Home the DHCP server unless you intentionally want to replace the router DHCP.

## If Something Breaks

- Open the AdGuard Home query log.
- Find the blocked domain.
- Add an allowlist rule for that domain.
- If the whole network is affected, change router DNS back to `192.168.15.1` or public DNS temporarily.
