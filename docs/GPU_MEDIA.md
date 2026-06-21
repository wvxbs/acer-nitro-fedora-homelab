# GPU, Plex and Video Workloads

## Strategy

Plan A is not PCI passthrough. Plan A is:

```text
Proxmox host NVIDIA driver
  -> /dev/nvidia* exposed to privileged LXC
  -> Plex/Jellyfin uses NVENC/NVDEC inside LXC
```

This is intentionally less flashy than VM passthrough and much more realistic for a laptop dGPU.

## Validate NVIDIA

After reboot on the Proxmox host:

```bash
nvidia-smi
```

Inside CT `media`:

```bash
pct exec 120 -- nvidia-smi
```

If host `nvidia-smi` fails:

- Check Secure Boot. Disable it unless you want to manage module signing.
- Confirm the NVIDIA device appears with `lspci -nn | grep -i nvidia`.
- Reboot once after driver installation.
- Check DKMS logs with `dkms status` and `journalctl -k`.

If CT `nvidia-smi` fails but host works:

- Check `/etc/pve/lxc/120.conf` has the `homelab-nvidia` block.
- Restart the CT: `pct stop 120 && pct start 120`.
- Confirm device nodes exist on host: `ls -l /dev/nvidia* /dev/dri`.

## Plex Hardware Transcoding

Requirements:

- Plex Pass.
- Hardware transcoding enabled in Plex settings.
- Plex running inside the media CT.
- `/transcode` mapped to SSD-backed appdata.

Watch GPU activity:

```bash
watch -n 1 nvidia-smi
```

## Upscaling

The GTX 1650 is useful for NVENC/NVDEC and small GPU jobs. It is not a miracle card for heavy AI upscaling. Good later additions:

- Tdarr or Unmanic in a separate CT/VM for library processing.
- ffmpeg jobs with NVENC/NVDEC.
- Video2X only for selective batch jobs.

## VM Passthrough

GPU passthrough to a VM is plan B. Before trying it, collect:

```bash
find /sys/kernel/iommu_groups/ -type l | sort -V
lspci -nnk | grep -A3 -Ei 'nvidia|vga|3d'
```

Only attempt passthrough if the IOMMU groups are sane and you are prepared to debug VBIOS/Optimus behavior.
