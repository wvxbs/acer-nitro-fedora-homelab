# Monitoring

The quick web monitor is Glances:

```text
https://glances.nitro.lan
```

It is the browser-friendly equivalent of `btop`/`bashtop` for this homelab. It
shows CPU, memory, disk, network, processes and Docker containers. The container
also receives NVIDIA runtime flags so compatible GPU metrics can appear when the
Glances image and host driver expose them.

Start it with the ops profile:

```bash
cd /opt/homelab
docker compose --profile ops up -d glances
```

For direct CLI checks on the host:

```bash
nvidia-smi
docker stats
free -h
df -h
```

If GPU data is missing from Glances, `nvidia-smi` remains the source of truth for
GTX 1650 utilization, VRAM, temperature and power state.

The homelab also exposes a tiny NVIDIA-specific page backed by `nvidia-smi`:

```text
https://gpu.nitro.lan
https://gpu.nitro.lan/json
```

This is intentionally simpler than a full metrics stack and is meant for quick
checks from a phone or browser.
