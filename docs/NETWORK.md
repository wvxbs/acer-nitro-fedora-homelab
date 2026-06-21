# Network Plan

## Default

Use Tailscale on the Proxmox host. This avoids opening ports on the Vivo router or the Wi-Fi 6E router.

Access patterns:

- Proxmox web UI: LAN IP or Tailscale IP, port `8006`.
- Plex: media CT LAN IP or Tailscale route, port `32400`.
- SSH: Tailscale SSH or normal SSH to host.

## Two Routers

Your network has a router in the office and another router at home. The low-friction plan is:

- Put the Acer on Ethernet when possible.
- Keep services reachable by Tailscale.
- Avoid port-forwarding.
- Optional later improvement: make the home router AP/bridge if it supports that cleanly.

## Host vs CT

Tailscale on the host is enough for administration. If you want direct MagicDNS names per service, install Tailscale inside the CT later, but start simple.

## Firewall

Proxmox normally exposes its web UI on `8006`. Do not expose this to the public internet. Keep admin access on LAN/Tailscale.
