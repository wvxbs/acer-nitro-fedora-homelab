# Monitoring

The quick web monitor is Glances:

```text
https://glances.nitro.lan
```

It is the browser-friendly equivalent of `btop`/`bashtop` for this homelab. It
shows CPU, memory, disk, network, processes and Docker containers. The container
also receives NVIDIA runtime flags so compatible GPU metrics can appear when the
Glances image and host driver expose them.

Start the monitoring services with the ops profile:

```bash
cd /opt/homelab
docker compose --profile ops up -d glances performance-web
```

For direct CLI checks on the host:

```bash
nvidia-smi
docker stats
free -h
df -h
```

If GPU data is missing from Glances, `nvidia-smi` remains the CLI source of truth
for GTX 1650 utilization, VRAM, temperature and power state.

The homelab exposes one consolidated telemetry page:

```text
https://performance.nitro.lan
https://performance.nitro.lan/api
```

It shows CPU, NVIDIA GPU, RAM, VRAM, battery, disks, network, temperatures,
processes, containers and lightweight browser-side charts. `https://gpu.nitro.lan`
is kept as a compatibility alias to the same page.

The repo also keeps the latest standalone `/opt/homelab/performance/server.py`
snapshot under `compose/performance/server.py`, and the current Compose service
uses that file directly.
