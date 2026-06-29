# Network Plan

Your topology sounds like:

```text
Internet
  |
Vivo router in office
  |
Cat 6/6e cable
  |
Home Wi-Fi 6E router
  |
Nitro homelab + home machines
```

## Recommended Setup

Use Ethernet as the primary Nitro path. It is more stable for Jellyfin, Docker pulls, model downloads and big file transfers. Keep Wi-Fi connected only as a high-metric fallback:

```text
enp7s0: 192.168.15.8/24, default route metric 100
wlp8s0: DHCP, default route metric 600
```

To reapply the intended NetworkManager profiles:

```bash
sudo ./scripts/55-network-failover.sh
```

Use Tailscale for access across both sides of the network without opening ports:

```bash
sudo tailscale up --ssh
tailscale ip -4
```

Then access:

- SSH: `ssh user@nitro-homelab` if MagicDNS is enabled, or `ssh user@TAILSCALE_IP`.
- Open WebUI: `http://TAILSCALE_IP:3000`.
- Portainer: `https://TAILSCALE_IP:9443`.

The bootstrap opens these ports in the Fedora firewall: `22/tcp`, `32400/tcp`, `3000/tcp`, `9443/tcp`, `9999/tcp`, `11434/tcp`, plus mDNS. That is local host firewall only; it does not open router/NAT access from the internet.

## If You Want Pure LAN Access From Office to Home

That usually needs one of these:

- Put the home router in AP/bridge mode, so everything is one LAN.
- Add a static route on the Vivo router pointing the home subnet to the home router.
- Avoid double NAT by making the home router the only router.

Those options depend on router firmware and are more annoying than Tailscale. This kit keeps the router config minimal.

## Local Names

The bootstrap installs Avahi/mDNS, so from many devices on the same LAN:

```text
nitro-homelab.local
```

Across Tailscale, prefer MagicDNS.
