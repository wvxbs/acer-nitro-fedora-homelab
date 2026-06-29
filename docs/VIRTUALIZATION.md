# Virtualization

This homelab can run VMs with Fedora's native KVM/QEMU/libvirt stack.

## Install

```bash
sudo ./scripts/75-virtualization.sh
```

After the script finishes, log out and back in so your user receives the
`libvirt` and `kvm` group membership.

## What Gets Installed

- KVM/QEMU and libvirt for running the VMs.
- `virt-install`, `virt-manager`, and `virt-viewer`.
- `cockpit-machines` so VMs can be managed from Cockpit.
- OVMF UEFI firmware and software TPM packages for modern guests.
- The default libvirt NAT network.

## Manage VMs

Open Cockpit from another machine:

```text
https://nitro-homelab:9090
```

If local DNS is not configured, use the Fedora host IP instead:

```bash
hostname -I
```

Then open:

```text
https://HOST_IP:9090
```

Go to **Virtual Machines** to create, start, stop, and inspect VMs.

## Windows Client App

For a desktop-style client on Windows, install **virt-viewer**, also called
**Remote Viewer**. It can open SPICE/VNC console files launched from Cockpit.

Recommended flow:

1. Open Cockpit in the Windows browser.
2. Go to **Virtual Machines**.
3. Open the VM console.
4. Use the external viewer / desktop viewer option when available.
5. Open the downloaded `.vv` file with Remote Viewer.

This keeps the VM running on Fedora while the screen, keyboard, and mouse are
used from the Windows client.

## Guest Access Options

- Linux VMs: use SSH for server-style access and SPICE/Remote Viewer for GUI.
- Modern Windows VMs: use SPICE/Remote Viewer for install and RDP after setup.
- Windows XP: keep it isolated. Prefer NAT networking, avoid direct internet,
  and do not expose XP RDP to the internet.

## Remote Access Safety

Do not expose SPICE, VNC, or RDP ports directly to the public internet. Use
LAN access or a VPN such as Tailscale/WireGuard.
