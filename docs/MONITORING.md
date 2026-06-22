# Monitoring

The homelab exposes one consolidated performance endpoint:

```text
https://performance.nitro.lan
```

It replaces the older split between Glances and the NVIDIA-only page. The page is intentionally simple and mobile-friendly, but keeps the important "bashtop-like" information in one place:

- CPU utilization, load average and estimated package power via Intel RAPL when the host exposes it.
- Memory and disk usage.
- NVIDIA GTX 1650 utilization, VRAM, temperature and power via `nvidia-smi`.
- Host temperature sensors exposed through `/sys/class/thermal`.
- Active Docker containers through the read-only Docker socket.
- Short in-browser history for CPU, GPU and memory.

Start it with the ops profile:

```bash
cd /opt/homelab
docker compose --profile ops up -d performance portainer dozzle
```

For direct CLI checks on the host:

```bash
nvidia-smi
docker stats
free -h
df -h
```

If CPU package power shows `n/d`, the host kernel did not expose Intel RAPL data to the container. GPU power and temperature still come from `nvidia-smi`.
