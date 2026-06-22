# Monitoring

The homelab exposes a consolidated performance endpoint:

```text
https://performance.nitro.lan
```

It shows the compact dashboard: CPU per core, load, CPU package power, frequency, memory, disk, network, disk I/O, temperatures, Docker containers, NVIDIA GTX 1650 data and Intel iGPU state.

For richer process inspection, use the Glances page linked from the dashboard:

```text
https://processes.nitro.lan
```

Start the ops profile:

```bash
cd /opt/homelab
docker compose --profile ops up -d performance glances portainer dozzle
```

Useful direct checks on the host:

```bash
nvidia-smi
docker stats
free -h
df -h
```

Notes:

- NVIDIA polling is cached by the dashboard to reduce needless GPU wakeups.
- Intel iGPU data comes from read-only i915 debugfs when available.
- CPU package power comes from Intel RAPL.
- If NVIDIA remains in `P0` while idle, reboot once after `scripts/35-power-tuning.sh` so `NVreg_DynamicPowerManagement=0x02` is applied when the module loads.
