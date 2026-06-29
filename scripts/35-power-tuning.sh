#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "${SCRIPT_DIR}/lib.sh"

log "Applying conservative power tuning"

if [[ -d /sys/devices/system/cpu ]]; then
  for governor in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    [[ -w "${governor}" ]] || continue
    echo powersave >"${governor}" || true
  done

  for preference in /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference; do
    [[ -w "${preference}" ]] || continue
    echo balance_power >"${preference}" || true
  done
fi

cat >/etc/modprobe.d/nvidia-power-management.conf <<'EOF'
# Allow NVIDIA notebook dGPU runtime D3 / dynamic power management when idle.
# Takes full effect after the nvidia kernel module is reloaded or the host reboots.
options nvidia NVreg_DynamicPowerManagement=0x02
EOF

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi -pm 0 || true
fi

if [[ "${1:-}" != "--no-systemd" ]] && command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
  cat >/etc/systemd/system/nitro-power-tuning.service <<EOF
[Unit]
Description=Nitro homelab conservative power tuning
After=multi-user.target

[Service]
Type=oneshot
ExecStart=${SCRIPT_DIR}/35-power-tuning.sh --no-systemd

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable nitro-power-tuning.service >/dev/null 2>&1 || true
fi

log "Power tuning applied. Reboot or reload NVIDIA modules for runtime D3 changes."
