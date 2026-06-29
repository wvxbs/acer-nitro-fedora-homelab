#!/usr/bin/env python3
import json
import os
<<<<<<< HEAD
import re
=======
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
import socket
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

<<<<<<< HEAD

HOST_PROC = Path(os.getenv("NITRO_PROC_PATH", "/host/proc"))
HOST_SYS = Path(os.getenv("NITRO_SYS_PATH", "/host/sys"))
HOST_ROOT = Path(os.getenv("NITRO_ROOT_PATH", "/host/root"))
HOST_DEBUG = Path(os.getenv("NITRO_DEBUG_PATH", "/host/debug"))
PORT = int(os.getenv("PORT", "9837"))
NVIDIA_POLL_SECONDS = int(os.getenv("NVIDIA_POLL_SECONDS", "5"))
STARTED = time.time()
HZ = os.sysconf("SC_CLK_TCK")
PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")

LAST_CPU = None
LAST_RAPL = {}
LAST_NET = None
LAST_DISK_IO = None
=======
HOST_PROC = Path(os.getenv("HOST_PROC", "/host/proc"))
HOST_SYS = Path(os.getenv("HOST_SYS", "/host/sys"))
HOST_DEBUG = Path(os.getenv("HOST_DEBUG", "/host/debug"))
PORT = int(os.getenv("PORT", "9837"))
NVIDIA_POLL_SECONDS = int(os.getenv("NVIDIA_POLL_SECONDS", "30"))
STARTED = time.time()
HZ = os.sysconf(os.sysconf_names.get("SC_CLK_TCK", "SC_CLK_TCK")) if hasattr(os, "sysconf") else 100
LAST_CPU = None
LAST_RAPL = None
LAST_NET = None
LAST_DISK = None
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
LAST_PROC = {}
LAST_GPU = None
LAST_GPU_TIME = 0


def read_text(path, default=""):
    try:
<<<<<<< HEAD
        return Path(path).read_text(errors="replace").strip()
=======
        return Path(path).read_text().strip()
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
    except Exception:
        return default


<<<<<<< HEAD
def number(value):
    try:
        raw = str(value).strip()
        if raw.upper() in {"", "N/A", "[N/A]", "NOT SUPPORTED"}:
            return None
        return float(raw)
    except Exception:
        return None


def pct(part, total):
    return round(part / total * 100, 1) if total else None


def host_path(path):
    if path == "/":
        return HOST_ROOT
    return HOST_ROOT / path.lstrip("/")
=======
def pct(part, total):
    return round(part / total * 100, 1) if total else 0


def fmt_bytes(value):
    value = float(value or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9


def cpu_snapshot():
    rows = []
    for line in read_text(HOST_PROC / "stat").splitlines():
        if not line.startswith("cpu"):
            continue
        parts = line.split()
<<<<<<< HEAD
        values = [int(v) for v in parts[1:]]
        idle = values[3] + values[4]
        rows.append((parts[0], idle, sum(values)))
=======
        name = parts[0]
        vals = [int(v) for v in parts[1:]]
        idle = vals[3] + vals[4]
        total = sum(vals)
        rows.append((name, idle, total))
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
    return rows


def cpu_sample():
    global LAST_CPU
    now = cpu_snapshot()
    if LAST_CPU is None:
        LAST_CPU = now
<<<<<<< HEAD
        return {"total": None, "cores": []}
    prev = {name: (idle, total) for name, idle, total in LAST_CPU}
    LAST_CPU = now
    cores = []
    total_percent = None
    for name, idle, total in now:
        last_idle, last_total = prev.get(name, (idle, total))
        dt = max(total - last_total, 1)
        value = round((1 - (idle - last_idle) / dt) * 100, 1)
=======
        return {"total": 0.0, "cores": []}
    prev = {name: (idle, total) for name, idle, total in LAST_CPU}
    LAST_CPU = now
    cores = []
    total_percent = 0.0
    for name, idle, total in now:
        last_idle, last_total = prev.get(name, (idle, total))
        dt = max(total - last_total, 1)
        di = idle - last_idle
        value = round((1 - di / dt) * 100, 1)
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
        if name == "cpu":
            total_percent = value
        else:
            cores.append({"name": name.replace("cpu", ""), "percent": value})
    return {"total": total_percent, "cores": cores}


def cpu_freq_sample():
    freqs = []
    for path in sorted(HOST_SYS.glob("devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq")):
<<<<<<< HEAD
        value = number(read_text(path))
        if value:
            freqs.append(value / 1000)
=======
        try:
            freqs.append(int(read_text(path)) / 1000)
        except Exception:
            pass
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
    if not freqs:
        return None
    return {"avg_mhz": round(sum(freqs) / len(freqs)), "max_mhz": round(max(freqs)), "min_mhz": round(min(freqs))}


<<<<<<< HEAD
def memory_sample():
=======
def mem_sample():
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
    items = {}
    for line in read_text(HOST_PROC / "meminfo").splitlines():
        key, value = line.split(":", 1)
        items[key] = int(value.strip().split()[0]) * 1024
    total = items.get("MemTotal", 0)
    available = items.get("MemAvailable", 0)
    used = total - available
    swap_total = items.get("SwapTotal", 0)
    swap_free = items.get("SwapFree", 0)
    return {
        "total": total,
        "used": used,
        "available": available,
        "percent": pct(used, total),
        "swap_total": swap_total,
        "swap_used": swap_total - swap_free,
        "swap_percent": pct(swap_total - swap_free, swap_total),
    }


def load_sample():
<<<<<<< HEAD
    one, five, fifteen, *_ = read_text(HOST_PROC / "loadavg", "0 0 0").split()
    return {"1m": float(one), "5m": float(five), "15m": float(fifteen)}
=======
    data = read_text(HOST_PROC / "loadavg", "0 0 0").split()
    return {"1m": float(data[0]), "5m": float(data[1]), "15m": float(data[2])}
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9


def uptime_sample():
    return round(float(read_text(HOST_PROC / "uptime", "0").split()[0]))


<<<<<<< HEAD
def mounts_sample():
    ignore_fs = {"autofs", "binfmt_misc", "bpf", "cgroup", "cgroup2", "configfs", "debugfs", "devpts", "devtmpfs", "efivarfs", "fusectl", "hugetlbfs", "mqueue", "nsfs", "overlay", "proc", "pstore", "rpc_pipefs", "securityfs", "selinuxfs", "squashfs", "sysfs", "tmpfs", "tracefs"}
    mounts = []
    seen = set()
    for line in read_text(HOST_PROC / "1/mounts", read_text(HOST_PROC / "mounts")).splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        device, mountpoint, fs_type = parts[:3]
        if fs_type in ignore_fs or mountpoint.startswith(("/proc", "/sys", "/dev", "/run/docker", "/var/lib/docker")):
            continue
        if device.startswith(("tmpfs", "overlay", "none")):
            continue
        try:
            st = os.statvfs(host_path(mountpoint))
        except Exception:
            continue
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = total - free
        key = (device, mountpoint)
        if total <= 0 or key in seen:
            continue
        seen.add(key)
        mounts.append({"device": device, "mount": mountpoint, "fs": fs_type, "total": total, "used": used, "free": free, "percent": pct(used, total)})
    mounts.sort(key=lambda item: item["percent"] or 0, reverse=True)
    return mounts[:12]
=======
def disk_sample():
    st = os.statvfs("/")
    total = st.f_blocks * st.f_frsize
    free = st.f_bavail * st.f_frsize
    used = total - free
    return {"total": total, "used": used, "free": free, "percent": pct(used, total)}
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9


def disk_io_snapshot():
    devices = {}
    for line in read_text(HOST_PROC / "diskstats").splitlines():
        parts = line.split()
        if len(parts) < 14:
            continue
        name = parts[2]
        if name.startswith(("loop", "ram", "zram")):
            continue
<<<<<<< HEAD
        if re.search(r"\d+$", name) and not name.startswith("nvme"):
            continue
        devices[name] = {"read_bytes": int(parts[5]) * 512, "write_bytes": int(parts[9]) * 512}
=======
        if any(name.endswith(str(i)) for i in range(10)) and not name.startswith("nvme"):
            continue
        read_sectors = int(parts[5])
        write_sectors = int(parts[9])
        devices[name] = {"read_bytes": read_sectors * 512, "write_bytes": write_sectors * 512}
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
    return devices


def disk_io_sample():
<<<<<<< HEAD
    global LAST_DISK_IO
    now_time = time.time()
    now = disk_io_snapshot()
    if LAST_DISK_IO is None:
        LAST_DISK_IO = (now_time, now)
        return {"read_bps": 0, "write_bps": 0, "devices": []}
    last_time, last = LAST_DISK_IO
    LAST_DISK_IO = (now_time, now)
    dt = max(now_time - last_time, 0.001)
    devices = []
    read_total = write_total = 0
=======
    global LAST_DISK
    now_time = time.time()
    now = disk_io_snapshot()
    if LAST_DISK is None:
        LAST_DISK = (now_time, now)
        return {"read_bps": 0, "write_bps": 0, "devices": []}
    last_time, last = LAST_DISK
    LAST_DISK = (now_time, now)
    dt = max(now_time - last_time, 0.001)
    read_total = write_total = 0
    devices = []
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
    for name, item in now.items():
        prev = last.get(name, item)
        rb = max(item["read_bytes"] - prev["read_bytes"], 0) / dt
        wb = max(item["write_bytes"] - prev["write_bytes"], 0) / dt
        read_total += rb
        write_total += wb
<<<<<<< HEAD
        devices.append({"name": name, "read_bps": round(rb), "write_bps": round(wb)})
    devices.sort(key=lambda i: i["read_bps"] + i["write_bps"], reverse=True)
=======
        if rb or wb:
            devices.append({"name": name, "read_bps": round(rb), "write_bps": round(wb)})
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
    return {"read_bps": round(read_total), "write_bps": round(write_total), "devices": devices[:8]}


def net_snapshot():
    data = {}
    for line in read_text(HOST_PROC / "net/dev").splitlines()[2:]:
        iface, raw = line.split(":", 1)
        iface = iface.strip()
        if iface == "lo":
            continue
        parts = raw.split()
        data[iface] = {"rx": int(parts[0]), "tx": int(parts[8])}
    return data


<<<<<<< HEAD
def network_sample():
=======
def net_sample():
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
    global LAST_NET
    now_time = time.time()
    now = net_snapshot()
    if LAST_NET is None:
        LAST_NET = (now_time, now)
        return {"rx_bps": 0, "tx_bps": 0, "interfaces": []}
    last_time, last = LAST_NET
    LAST_NET = (now_time, now)
    dt = max(now_time - last_time, 0.001)
<<<<<<< HEAD
    interfaces = []
    rx_total = tx_total = 0
=======
    rx_total = tx_total = 0
    interfaces = []
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
    for iface, item in now.items():
        prev = last.get(iface, item)
        rx = max(item["rx"] - prev["rx"], 0) / dt
        tx = max(item["tx"] - prev["tx"], 0) / dt
        rx_total += rx
        tx_total += tx
        interfaces.append({"name": iface, "rx_bps": round(rx), "tx_bps": round(tx)})
    interfaces.sort(key=lambda i: i["rx_bps"] + i["tx_bps"], reverse=True)
<<<<<<< HEAD
    return {"rx_bps": round(rx_total), "tx_bps": round(tx_total), "interfaces": interfaces[:8]}


def rapl_power_sample():
    global LAST_RAPL
    now = time.time()
    readings = {}
    for path in HOST_SYS.glob("class/powercap/intel-rapl:*/energy_uj"):
        name = read_text(path.parent / "name", path.parent.name)
        value = number(read_text(path))
        if value is not None:
            readings[name] = value
    powers = []
    for name, energy in readings.items():
        previous = LAST_RAPL.get(name)
        watts = None
        if previous:
            last_time, last_energy = previous
            delta = energy - last_energy
            if delta >= 0:
                watts = round(delta / max(now - last_time, 0.001) / 1_000_000, 1)
        LAST_RAPL[name] = (now, energy)
        powers.append({"name": name, "watts": watts})
    package = next((p["watts"] for p in powers if p["name"] == "package-0"), None)
    if package is None and powers:
        known = [p["watts"] for p in powers if p["watts"] is not None]
        package = round(sum(known), 1) if known else None
    return {"package_w": package, "domains": powers}


def hwmon_temps():
    temps = []
    for hwmon in HOST_SYS.glob("class/hwmon/hwmon*"):
        chip = read_text(hwmon / "name", hwmon.name)
        for temp_input in hwmon.glob("temp*_input"):
            value = number(read_text(temp_input))
            if value is None:
                continue
            index = temp_input.name.replace("temp", "").replace("_input", "")
            label = read_text(hwmon / f"temp{index}_label", chip)
            celsius = round(value / 1000, 1)
            if -20 <= celsius <= 130:
                temps.append({"name": f"{chip} {label}".strip(), "c": celsius, "source": "hwmon"})
    for zone in HOST_SYS.glob("class/thermal/thermal_zone*"):
        value = number(read_text(zone / "temp"))
        label = read_text(zone / "type", zone.name)
        if value is not None:
            celsius = round(value / 1000, 1)
            if -20 <= celsius <= 130:
                temps.append({"name": label, "c": celsius, "source": "thermal"})
    unique = {}
    for item in temps:
        unique[(item["name"], item["c"])] = item
    return sorted(unique.values(), key=lambda x: x["c"], reverse=True)


def block_device_temps(temps):
    rows = []
    for hwmon in HOST_SYS.glob("class/hwmon/hwmon*"):
        chip = read_text(hwmon / "name", hwmon.name).lower()
        if not any(token in chip for token in ("nvme", "drivetemp")):
            continue
        c_values = []
        for path in hwmon.glob("temp*_input"):
            value = number(read_text(path))
            if value is not None:
                c_values.append(round(value / 1000, 1))
        if not c_values:
            continue
        device = chip
        link = hwmon / "device"
        try:
            real = link.resolve()
            device = real.name if real.name else chip
        except Exception:
            pass
        rows.append({"device": device, "temp_c": max(c_values), "source": chip})
    if rows:
        return rows
    for item in temps:
        low = item["name"].lower()
        if "nvme" in low or "drivetemp" in low:
            rows.append({"device": item["name"], "temp_c": item["c"], "source": item["source"]})
    return rows[:8]


def network_temps(temps):
    rows = []
    for item in temps:
        low = item["name"].lower()
        if any(token in low for token in ("iwlwifi", "wifi", "wlan", "ath", "mt76", "realtek", "rtl", "ethernet", "nic")):
            rows.append(item)
    return rows[:6]
=======
    return {"rx_bps": round(rx_total), "tx_bps": round(tx_total), "interfaces": interfaces[:6]}


def cpu_power_watts():
    global LAST_RAPL
    readings = []
    for path in HOST_SYS.glob("class/powercap/intel-rapl:*/energy_uj"):
        try:
            readings.append(int(read_text(path)))
        except Exception:
            pass
    now = time.time()
    if not readings:
        return None
    energy = sum(readings)
    if LAST_RAPL is None:
        LAST_RAPL = (now, energy)
        return None
    last_time, last_energy = LAST_RAPL
    LAST_RAPL = (now, energy)
    delta = energy - last_energy
    if delta < 0:
        return None
    return round(delta / max(now - last_time, 0.001) / 1_000_000, 1)


def temps_sample():
    temps = []
    for zone in HOST_SYS.glob("class/thermal/thermal_zone*"):
        temp = read_text(zone / "temp")
        label = read_text(zone / "type", zone.name)
        try:
            value = round(int(temp) / 1000, 1)
            if value > 0:
                temps.append({"name": label, "c": value})
        except Exception:
            pass
    return sorted(temps, key=lambda x: x["c"], reverse=True)[:10]


def safe_float(value):
    try:
        if value in ("", "N/A", "[N/A]"):
            return None
        return float(value)
    except Exception:
        return None
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9


def gpu_sample():
    global LAST_GPU, LAST_GPU_TIME
    now = time.time()
    if LAST_GPU is not None and now - LAST_GPU_TIME < NVIDIA_POLL_SECONDS:
        cached = dict(LAST_GPU)
        cached["cached_s"] = round(now - LAST_GPU_TIME)
        return cached
<<<<<<< HEAD
    query = "name,driver_version,pstate,temperature.gpu,power.draw,power.limit,utilization.gpu,utilization.memory,memory.used,memory.total,clocks.current.graphics,clocks.current.memory,fan.speed"
    cmd = ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=2).strip()
    except Exception:
        return LAST_GPU
    line = out.splitlines()[0] if out else ""
    fields = [x.strip() for x in line.split(",")]
    while len(fields) < 13:
        fields.append("")
    mem_used = number(fields[8]) or 0
    mem_total = number(fields[9]) or 0
    LAST_GPU_TIME = now
    LAST_GPU = {
        "name": fields[0],
        "driver_version": fields[1],
        "pstate": fields[2],
        "temp_c": number(fields[3]),
        "power_w": number(fields[4]),
        "power_limit_w": number(fields[5]),
        "util_percent": number(fields[6]) or 0,
        "memory_util_percent": number(fields[7]),
        "memory_used_mb": mem_used,
        "memory_total_mb": mem_total,
        "memory_percent": pct(mem_used, mem_total),
        "graphics_clock_mhz": number(fields[10]),
        "memory_clock_mhz": number(fields[11]),
        "fan_percent": number(fields[12]),
=======
    query = "name,pstate,temperature.gpu,power.draw,power.limit,utilization.gpu,utilization.memory,memory.used,memory.total,clocks.current.graphics,clocks.current.memory"
    cmd = ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"]
    try:
        out = subprocess.check_output(cmd, text=True, timeout=2).strip()
    except Exception:
        return LAST_GPU
    fields = [x.strip() for x in out.splitlines()[0].split(",")]
    while len(fields) < 11:
        fields.append("")
    LAST_GPU_TIME = now
    LAST_GPU = {
        "name": fields[0],
        "pstate": fields[1],
        "temp_c": safe_float(fields[2]),
        "power_w": safe_float(fields[3]),
        "power_limit_w": safe_float(fields[4]),
        "util_percent": safe_float(fields[5]) or 0,
        "memory_util_percent": safe_float(fields[6]) or 0,
        "memory_used_mb": safe_float(fields[7]) or 0,
        "memory_total_mb": safe_float(fields[8]) or 0,
        "graphics_clock_mhz": safe_float(fields[9]),
        "memory_clock_mhz": safe_float(fields[10]),
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
        "cached_s": 0,
    }
    return LAST_GPU


def parse_mhz_line(text, label):
    for line in text.splitlines():
        if line.strip().startswith(label):
<<<<<<< HEAD
            return number(line.split(":", 1)[1].strip().split()[0])
=======
            value = line.split(":", 1)[1].strip().split()[0]
            try:
                return float(value)
            except Exception:
                return None
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
    return None


def intel_igpu_sample():
<<<<<<< HEAD
    candidates = sorted((HOST_DEBUG / "dri").glob("*/i915_frequency_info"))
    base = candidates[0].parent if candidates else HOST_DEBUG / "dri" / "0000:00:02.0"
=======
    base = HOST_DEBUG / "dri" / "0000:00:02.0"
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
    freq = read_text(base / "i915_frequency_info")
    drpc = read_text(base / "gt0" / "drpc")
    rpm = read_text(base / "i915_runtime_pm_status")
    if not freq and not drpc and not rpm:
<<<<<<< HEAD
        return {"name": "Intel iGPU", "available": False}
    rc_state = None
    gpu_idle = None
    pci_power = None
    for line in drpc.splitlines():
        if line.startswith("Current RC state:"):
            rc_state = line.split(":", 1)[1].strip()
=======
        return {"name": "Intel UHD Graphics 630", "available": False}
    rc_state = None
    for line in drpc.splitlines():
        if line.startswith("Current RC state:"):
            rc_state = line.split(":", 1)[1].strip()
    gpu_idle = None
    pci_power = None
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
    for line in rpm.splitlines():
        if line.startswith("GPU idle:"):
            gpu_idle = line.split(":", 1)[1].strip()
        if line.startswith("PCI device power state:"):
            pci_power = line.split(":", 1)[1].strip()
    return {
<<<<<<< HEAD
        "name": "Intel iGPU",
=======
        "name": "Intel UHD Graphics 630",
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
        "available": True,
        "current_mhz": parse_mhz_line(freq, "Current freq"),
        "actual_mhz": parse_mhz_line(freq, "Actual freq"),
        "min_mhz": parse_mhz_line(freq, "Min freq"),
        "max_mhz": parse_mhz_line(freq, "Max freq"),
        "boost_mhz": parse_mhz_line(freq, "Boost freq"),
        "rc_state": rc_state,
        "gpu_idle": gpu_idle,
        "pci_power_state": pci_power,
    }


<<<<<<< HEAD
def battery_sample():
    batteries = []
    adapters = []
    for supply in sorted((HOST_SYS / "class/power_supply").glob("*")):
        supply_type = read_text(supply / "type", "").lower()
        if supply_type == "battery":
            energy_now = number(read_text(supply / "energy_now"))
            energy_full = number(read_text(supply / "energy_full"))
            energy_design = number(read_text(supply / "energy_full_design"))
            charge_now = number(read_text(supply / "charge_now"))
            charge_full = number(read_text(supply / "charge_full"))
            charge_design = number(read_text(supply / "charge_full_design"))
            voltage_now = number(read_text(supply / "voltage_now"))
            power_now = number(read_text(supply / "power_now"))
            current_now = number(read_text(supply / "current_now"))
            temp_raw = number(read_text(supply / "temp"))
            if power_now is None and current_now and voltage_now:
                power_now = current_now * voltage_now / 1_000_000
            if energy_now is None and charge_now and voltage_now:
                energy_now = charge_now * voltage_now / 1_000_000
            if energy_full is None and charge_full and voltage_now:
                energy_full = charge_full * voltage_now / 1_000_000
            if energy_design is None and charge_design and voltage_now:
                energy_design = charge_design * voltage_now / 1_000_000
            percent = number(read_text(supply / "capacity"))
            if percent is None:
                percent = pct(energy_now, energy_full)
            batteries.append({
                "name": supply.name,
                "status": read_text(supply / "status", "unknown"),
                "percent": percent,
                "power_w": round(power_now / 1_000_000, 2) if power_now else None,
                "energy_now_wh": round(energy_now / 1_000_000, 2) if energy_now else None,
                "energy_full_wh": round(energy_full / 1_000_000, 2) if energy_full else None,
                "voltage_v": round(voltage_now / 1_000_000, 2) if voltage_now else None,
                "cycle_count": number(read_text(supply / "cycle_count")),
                "health_percent": pct(energy_full, energy_design),
                "temp_c": round(temp_raw / 10, 1) if temp_raw else None,
            })
        elif supply_type in {"mains", "usb", "usb_c", "usb_pd"}:
            adapters.append({"name": supply.name, "online": read_text(supply / "online", "0") == "1", "type": supply_type})
    return {"batteries": batteries, "adapters": adapters}


=======
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
def decode_chunked(body):
    decoded = b""
    rest = body
    while rest:
        line, _, rest = rest.partition(b"\r\n")
        try:
            size = int(line.split(b";", 1)[0], 16)
        except ValueError:
            return body
        if size == 0:
            return decoded
        decoded += rest[:size]
        rest = rest[size + 2:]
    return decoded


def docker_request(path):
    sock_path = "/var/run/docker.sock"
    if not Path(sock_path).exists():
        return None
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(2)
    client.connect(sock_path)
    client.sendall(f"GET {path} HTTP/1.1\r\nHost: docker\r\nConnection: close\r\n\r\n".encode())
    chunks = []
    while True:
        data = client.recv(65536)
        if not data:
            break
        chunks.append(data)
    client.close()
    response = b"".join(chunks)
    header, _, body = response.partition(b"\r\n\r\n")
    if b" 200 " not in header.split(b"\r\n", 1)[0]:
        return None
    if b"transfer-encoding: chunked" in header.lower():
        body = decode_chunked(body)
    return json.loads(body.decode())


def docker_sample():
    try:
        containers = docker_request("/containers/json") or []
    except Exception:
        containers = []
    rows = []
    for item in containers:
<<<<<<< HEAD
        rows.append({"name": (item.get("Names") or [""])[0].lstrip("/"), "image": item.get("Image", ""), "status": item.get("Status", "")})
=======
        name = (item.get("Names") or [""])[0].lstrip("/")
        rows.append({"name": name, "image": item.get("Image", ""), "status": item.get("Status", "")})
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
    return rows


def processes_sample():
    global LAST_PROC
    now = time.time()
    current = {}
    rows = []
    for proc in HOST_PROC.iterdir():
        if not proc.name.isdigit():
            continue
        stat = read_text(proc / "stat")
        if not stat or ")" not in stat:
            continue
        try:
            pid = int(proc.name)
            comm = stat.split("(", 1)[1].rsplit(")", 1)[0]
            rest = stat.rsplit(")", 1)[1].split()
            ticks = int(rest[11]) + int(rest[12])
<<<<<<< HEAD
            rss = int(rest[21]) * PAGE_SIZE
=======
            rss_pages = int(rest[21])
            rss = rss_pages * os.sysconf("SC_PAGE_SIZE")
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
            current[pid] = (now, ticks)
            prev = LAST_PROC.get(pid)
            cpu = 0.0
            if prev:
                last_time, last_ticks = prev
                cpu = max(ticks - last_ticks, 0) / HZ / max(now - last_time, 0.001) * 100
<<<<<<< HEAD
            rows.append({"pid": pid, "name": comm[:36], "cpu_percent": round(cpu, 1), "rss": rss})
        except Exception:
            pass
    LAST_PROC = current
    return {"cpu": sorted(rows, key=lambda r: r["cpu_percent"], reverse=True)[:8], "memory": sorted(rows, key=lambda r: r["rss"], reverse=True)[:8]}
=======
            rows.append({"pid": pid, "name": comm[:32], "cpu_percent": round(cpu, 1), "rss": rss})
        except Exception:
            pass
    LAST_PROC = current
    by_cpu = sorted(rows, key=lambda r: r["cpu_percent"], reverse=True)[:8]
    by_mem = sorted(rows, key=lambda r: r["rss"], reverse=True)[:8]
    return {"cpu": by_cpu, "memory": by_mem}
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9


def collect():
    cpu = cpu_sample()
<<<<<<< HEAD
    power = rapl_power_sample()
    temps = hwmon_temps()
    mounts = mounts_sample()
    root_mount = next((mount for mount in mounts if mount["mount"] == "/"), None)
    return {
        "host": read_text(HOST_ROOT / "etc/hostname", read_text(HOST_PROC / "sys/kernel/hostname", socket.gethostname())),
=======
    return {
        "host": socket.gethostname(),
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
        "time": int(time.time()),
        "app_uptime_s": round(time.time() - STARTED),
        "host_uptime_s": uptime_sample(),
        "cpu_percent": cpu["total"],
        "cpu_cores": cpu["cores"],
        "cpu_frequency": cpu_freq_sample(),
<<<<<<< HEAD
        "cpu_power": power,
        "load": load_sample(),
        "memory": memory_sample(),
        "mounts": mounts,
        "disk": root_mount or (mounts[0] if mounts else None),
        "disk_io": disk_io_sample(),
        "disk_temps": block_device_temps(temps),
        "network": network_sample(),
        "network_temps": network_temps(temps),
        "temps": temps[:32],
        "gpu": gpu_sample(),
        "igpu": intel_igpu_sample(),
        "battery": battery_sample(),
        "containers": docker_sample(),
        "processes": processes_sample(),
        "links": {"glances": "http://glances.nitro.lan/", "homelab": "http://nitro.lan/"},
    }


HTML = r'''<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nitro Telemetria</title><style>
:root{color-scheme:dark;--bg:#07090c;--panel:#111820;--panel2:#17212b;--line:#2b3846;--text:#edf6ff;--muted:#91a4b7;--ok:#58d878;--warn:#f2c84b;--hot:#ff6969;--blue:#78a9ff;--cyan:#46d7d0;--violet:#b18cff}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:ui-sans-serif,system-ui,Segoe UI,Roboto,Arial;padding:14px}main{max-width:1440px;margin:0 auto}.top{display:flex;justify-content:space-between;gap:12px;align-items:end;margin:4px 0 14px}.actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}h1{font-size:26px;margin:0}a{color:var(--text);text-decoration:none}.button,.pill{display:inline-flex;align-items:center;border:1px solid var(--line);background:var(--panel2);border-radius:8px;color:var(--text)}.button{min-height:36px;padding:0 10px}.pill{padding:3px 7px;color:var(--muted);font-size:12px;margin:2px 4px 2px 0}small,.muted{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:10px}.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px;min-height:104px}.span3{grid-column:span 3}.span4{grid-column:span 4}.span5{grid-column:span 5}.span6{grid-column:span 6}.span7{grid-column:span 7}.span8{grid-column:span 8}.span12{grid-column:1/-1}.label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.value{font-size:30px;font-weight:780;margin:5px 0 3px;overflow-wrap:anywhere}.bar{height:8px;background:#080d12;border:1px solid #22303d;border-radius:99px;overflow:hidden}.fill{height:100%;width:0;background:linear-gradient(90deg,var(--ok),var(--warn),var(--hot))}.mini{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-top:8px}.core{height:24px;background:#0a1016;border:1px solid var(--line);border-radius:5px;position:relative;overflow:hidden}.core b{position:absolute;inset:0;background:#315f49}.core span{position:absolute;inset:4px;font-size:11px}.charts{display:grid;grid-template-columns:1fr;gap:10px}canvas{width:100%;height:210px;background:#080d12;border:1px solid var(--line);border-radius:8px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:10px}table{width:100%;border-collapse:collapse;font-size:13px}td,th{border-top:1px solid var(--line);padding:7px 0;text-align:left;vertical-align:top}td:last-child,th:last-child{text-align:right;color:var(--muted)}.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:8px;margin-top:8px}.tile{background:#0a1016;border:1px solid var(--line);border-radius:8px;padding:10px;min-height:78px}.tile .k{color:var(--muted);font-size:12px}.tile .t{font-size:24px;font-weight:800;margin-top:4px}.ok .t{color:var(--ok)}.warn .t{color:var(--warn)}.hot .t{color:var(--hot)}@media(max-width:980px){body{padding:10px}.top,.cols{display:block}.actions{justify-content:flex-start;margin-top:10px}.grid{display:block}.card{margin-bottom:10px}.mini{grid-template-columns:repeat(2,1fr)}canvas{height:180px}}
</style></head><body><main><div class="top"><div><h1>Nitro Telemetria</h1><small id="stamp">coletando...</small></div><div class="actions"><a class="button" href="http://glances.nitro.lan/">Glances</a><a class="button" href="http://nitro.lan/">Homelab</a><a class="button" href="/api">JSON</a></div></div><section class="grid">
<div class="card span3"><div class="label">CPU</div><div class="value" id="cpu">n/d</div><div class="bar"><div class="fill" id="cpuBar"></div></div><small id="load"></small><div class="mini" id="cores"></div></div>
<div class="card span3"><div class="label">CPU package</div><div class="value" id="cpuw">n/d</div><div id="freq"></div><small>potencia via RAPL quando exposto pelo host</small></div>
<div class="card span3"><div class="label">GPU NVIDIA</div><div class="value" id="gpu">n/d</div><div class="bar"><div class="fill" id="gpuBar"></div></div><small id="gpuMeta"></small></div>
<div class="card span3"><div class="label">GPU power / VRAM</div><div class="value" id="gpuw">n/d</div><div id="gpuMore"></div></div>
<div class="card span3"><div class="label">RAM</div><div class="value" id="ram">n/d</div><div class="bar"><div class="fill" id="ramBar"></div></div><small id="ramtxt"></small></div>
<div class="card span3"><div class="label">Bateria</div><div class="value" id="bat">n/d</div><div class="bar"><div class="fill" id="batBar"></div></div><small id="battxt"></small></div>
<div class="card span3"><div class="label">Disco principal</div><div class="value" id="disk">n/d</div><div class="bar"><div class="fill" id="diskBar"></div></div><small id="disktxt"></small></div>
<div class="card span3"><div class="label">Rede</div><div class="value" id="net">n/d</div><small id="nettxt"></small></div>
<div class="card span3"><div class="label">I/O disco</div><div class="value" id="io">n/d</div><small id="iotxt"></small></div>
<div class="card span3"><div class="label">Intel iGPU</div><div class="value" id="igpu">n/d</div><div id="igpuMore"></div></div>
<div class="card span6"><div class="label">Energia da bateria</div><div class="tiles" id="batteryTiles"></div></div>
<div class="card span12"><div class="label">Historico de carga, memoria e potencia</div><canvas id="chart" width="1360" height="230"></canvas></div>
<div class="card span12"><div class="label">Temperaturas</div><div class="tiles" id="tempTiles"></div><canvas id="tempChart" width="1360" height="190"></canvas></div>
<div class="card span6"><div class="label">Discos e particoes</div><table id="mounts"></table></div>
<div class="card span6"><div class="label">Temperatura de discos e rede</div><div class="cols"><table id="diskTemps"></table><table id="netTemps"></table></div></div>
<div class="card span6"><div class="label">Processos</div><div class="cols"><table id="procCpu"></table><table id="procMem"></table></div></div>
<div class="card span6"><div class="label">Containers</div><table id="containers"></table></div>
</section></main><script>
const hist=[],tempHist=[],$=id=>document.getElementById(id);const na=v=>v==null||Number.isNaN(v);const nb=v=>na(v)?'n/d':v;const gb=v=>na(v)?'n/d':(v/1024/1024/1024).toFixed(1)+' GB';const mb=v=>na(v)?'n/d':(v/1024/1024).toFixed(0)+' MB';const rate=v=>{if(na(v))return'n/d';if(v>1048576)return(v/1048576).toFixed(1)+' MB/s';if(v>1024)return(v/1024).toFixed(1)+' KB/s';return Math.round(v)+' B/s'};function bar(id,v){$(id).style.width=Math.max(0,Math.min(100,v||0))+'%'}function row(a,b){return`<tr><td>${a}</td><td>${b}</td></tr>`}function pct(v){return na(v)?'n/d':v+'%'}function tempClass(v){return na(v)?'':v>=85?'hot':v>=70?'warn':'ok'}function tile(k,v,sub,cls=''){return`<div class="tile ${cls}"><div class="k">${k}</div><div class="t">${v}</div><small>${sub||''}</small></div>`}
function draw(){const c=$('chart'),x=c.getContext('2d'),w=c.width,h=c.height;x.clearRect(0,0,w,h);x.strokeStyle='#2b3846';for(let i=0;i<=4;i++){x.beginPath();x.moveTo(0,i*h/4);x.lineTo(w,i*h/4);x.stroke()}function line(k,col,scale=100){x.strokeStyle=col;x.lineWidth=3;x.beginPath();hist.forEach((p,i)=>{const xx=i*(w/Math.max(hist.length-1,1)),yy=h-Math.min(100,(p[k]||0)/scale*100)*h/100;i?x.lineTo(xx,yy):x.moveTo(xx,yy)});x.stroke()}line('cpu','#58d878');line('gpu','#78a9ff');line('ram','#f2c84b');line('cpuw','#ff6969',60);line('gpuw','#b18cff',60);x.fillStyle='#91a4b7';x.fillText('CPU verde | GPU azul | RAM amarelo | CPU W vermelho | GPU W violeta',12,18)}
function drawTemps(){const c=$('tempChart'),x=c.getContext('2d'),w=c.width,h=c.height;x.clearRect(0,0,w,h);x.strokeStyle='#2b3846';for(let i=0;i<=4;i++){x.beginPath();x.moveTo(0,i*h/4);x.lineTo(w,i*h/4);x.stroke()}function line(k,col){x.strokeStyle=col;x.lineWidth=3;x.beginPath();tempHist.forEach((p,i)=>{const xx=i*(w/Math.max(tempHist.length-1,1)),yy=h-Math.min(100,p[k]||0)*h/100;i?x.lineTo(xx,yy):x.moveTo(xx,yy)});x.stroke()}line('cpu','#ff6969');line('gpu','#78a9ff');line('disk','#f2c84b');line('net','#46d7d0');x.fillStyle='#91a4b7';x.fillText('CPU vermelho | GPU azul | disco amarelo | rede ciano',12,18)}
function sensor(d,terms){return (d.temps||[]).find(t=>terms.some(m=>t.name.toLowerCase().includes(m)))?.c}
async function tick(){const d=await(await fetch('/api',{cache:'no-store'})).json();stamp.textContent=`${d.host} · ${new Date(d.time*1000).toLocaleString()} · uptime ${Math.round(d.host_uptime_s/3600)}h`;cpu.textContent=pct(d.cpu_percent);bar('cpuBar',d.cpu_percent);load.textContent=`load ${d.load['1m']} / ${d.load['5m']} / ${d.load['15m']}`;cores.innerHTML=(d.cpu_cores||[]).map(c=>`<div class="core"><b style="width:${c.percent}%"></b><span>${c.name}: ${c.percent}%</span></div>`).join('');cpuw.textContent=na(d.cpu_power?.package_w)?'n/d':d.cpu_power.package_w+' W';freq.innerHTML=d.cpu_frequency?`<span class="pill">avg ${d.cpu_frequency.avg_mhz} MHz</span><span class="pill">max ${d.cpu_frequency.max_mhz} MHz</span><span class="pill">min ${d.cpu_frequency.min_mhz} MHz</span>`:'<span class="pill">freq n/d</span>';ram.textContent=pct(d.memory.percent);bar('ramBar',d.memory.percent);ramtxt.textContent=`${gb(d.memory.used)} / ${gb(d.memory.total)} · swap ${pct(d.memory.swap_percent)}`;const disk0=d.disk||{};disk.textContent=pct(disk0.percent);bar('diskBar',disk0.percent);disktxt.textContent=`${disk0.mount||''} ${gb(disk0.used)} / ${gb(disk0.total)} livres ${gb(disk0.free)}`;net.textContent=rate((d.network.rx_bps||0)+(d.network.tx_bps||0));nettxt.textContent=`down ${rate(d.network.rx_bps)} · up ${rate(d.network.tx_bps)}`;io.textContent=rate((d.disk_io.read_bps||0)+(d.disk_io.write_bps||0));iotxt.textContent=`read ${rate(d.disk_io.read_bps)} · write ${rate(d.disk_io.write_bps)}`;
if(d.gpu){gpu.textContent=pct(d.gpu.util_percent);bar('gpuBar',d.gpu.util_percent);gpuMeta.textContent=`${d.gpu.name||'NVIDIA'} · ${d.gpu.pstate||'pstate n/d'} · driver ${d.gpu.driver_version||'n/d'}`;gpuw.textContent=na(d.gpu.power_w)?'n/d':d.gpu.power_w+' W';gpuMore.innerHTML=`<span class="pill">VRAM ${d.gpu.memory_used_mb}/${d.gpu.memory_total_mb} MB (${pct(d.gpu.memory_percent)})</span><span class="pill">mem util ${pct(d.gpu.memory_util_percent)}</span><span class="pill">${nb(d.gpu.temp_c)} C</span><span class="pill">gfx ${nb(d.gpu.graphics_clock_mhz)} MHz</span>`}else{gpu.textContent='n/d';gpuMeta.textContent='nvidia-smi indisponivel';gpuw.textContent='n/d';gpuMore.innerHTML=''}
if(d.igpu&&d.igpu.available){igpu.textContent=(d.igpu.actual_mhz??d.igpu.current_mhz??'n/d')+' MHz';igpuMore.innerHTML=`<span class="pill">${d.igpu.rc_state||'rc n/d'}</span><span class="pill">idle ${d.igpu.gpu_idle||'n/d'}</span><span class="pill">${d.igpu.pci_power_state||'power n/d'}</span>`}else{igpu.textContent='n/d';igpuMore.innerHTML='<span class="pill">debugfs i915 indisponivel</span>'}
const b=(d.battery?.batteries||[])[0];bat.textContent=b?pct(b.percent):'n/d';bar('batBar',b?.percent);battxt.textContent=b?`${b.status} · ${na(b.power_w)?'potencia n/d':b.power_w+' W'} · ${b.voltage_v||'n/d'} V`:'sem bateria exposta em /sys';batteryTiles.innerHTML=(d.battery?.batteries||[]).map(x=>tile(x.name,pct(x.percent),`${x.status} · ${x.energy_now_wh||'n/d'} / ${x.energy_full_wh||'n/d'} Wh`,tempClass(x.temp_c))+tile('Potencia',na(x.power_w)?'n/d':x.power_w+' W',`saude ${pct(x.health_percent)} · ciclos ${nb(x.cycle_count)}`)+tile('Voltagem',na(x.voltage_v)?'n/d':x.voltage_v+' V',na(x.temp_c)?'temp n/d':x.temp_c+' C',tempClass(x.temp_c))).join('')+(d.battery?.adapters||[]).map(a=>tile(a.name,a.online?'online':'offline',a.type,a.online?'ok':'')).join('')||tile('Bateria','n/d','nenhum power_supply de bateria encontrado');
const cpuTemp=sensor(d,['x86_pkg','package id','coretemp','k10temp']);const gpuTemp=d.gpu?.temp_c;const diskTemp=(d.disk_temps||[])[0]?.temp_c;const netTemp=(d.network_temps||[])[0]?.c;tempTiles.innerHTML=[tile('CPU package',na(cpuTemp)?'n/d':cpuTemp+' C','sensor de pacote/core',tempClass(cpuTemp)),tile('GPU NVIDIA',na(gpuTemp)?'n/d':gpuTemp+' C',na(d.gpu?.power_w)?'power n/d':d.gpu.power_w+' W',tempClass(gpuTemp)),tile('Disco',na(diskTemp)?'n/d':diskTemp+' C',(d.disk_temps||[])[0]?.device||'sensor n/d',tempClass(diskTemp)),tile('Placa de rede',na(netTemp)?'n/d':netTemp+' C',(d.network_temps||[])[0]?.name||'sensor n/d',tempClass(netTemp))].join('');
mounts.innerHTML='<tr><th>Mount</th><th>Uso</th></tr>'+((d.mounts||[]).map(m=>row(`${m.mount}<br><small>${m.device} · ${m.fs}</small>`,`${pct(m.percent)}<br><small>${gb(m.used)} / ${gb(m.total)}</small>`)).join('')||row('n/d',''));diskTemps.innerHTML='<tr><th>Disco</th><th>Temp</th></tr>'+((d.disk_temps||[]).map(t=>row(t.device,`${t.temp_c} C`)).join('')||row('sem sensor','n/d'));netTemps.innerHTML='<tr><th>Rede</th><th>Temp</th></tr>'+((d.network_temps||[]).map(t=>row(t.name,`${t.c} C`)).join('')||row('sem sensor','n/d'));containers.innerHTML='<tr><th>Container</th><th>Status</th></tr>'+((d.containers||[]).map(c=>row(c.name,c.status.replace('Up ',''))).join('')||row('sem acesso','n/d'));procCpu.innerHTML='<tr><th>CPU</th><th>%</th></tr>'+((d.processes.cpu||[]).map(p=>row(`${p.name} <span class="muted">${p.pid}</span>`,p.cpu_percent)).join(''));procMem.innerHTML='<tr><th>RAM</th><th>RSS</th></tr>'+((d.processes.memory||[]).map(p=>row(`${p.name} <span class="muted">${p.pid}</span>`,mb(p.rss))).join(''));
hist.push({cpu:d.cpu_percent||0,gpu:d.gpu?.util_percent||0,ram:d.memory.percent||0,cpuw:d.cpu_power?.package_w||0,gpuw:d.gpu?.power_w||0});tempHist.push({cpu:cpuTemp||0,gpu:gpuTemp||0,disk:diskTemp||0,net:netTemp||0});while(hist.length>180)hist.shift();while(tempHist.length>180)tempHist.shift();draw();drawTemps()}
tick().catch(e=>{stamp.textContent='erro: '+e});setInterval(()=>tick().catch(e=>{stamp.textContent='erro: '+e}),2500);
=======
        "cpu_power_w": cpu_power_watts(),
        "load": load_sample(),
        "memory": mem_sample(),
        "disk": disk_sample(),
        "disk_io": disk_io_sample(),
        "network": net_sample(),
        "temps": temps_sample(),
        "gpu": gpu_sample(),
        "igpu": intel_igpu_sample(),
        "containers": docker_sample(),
        "processes": processes_sample(),
    }


HTML = r'''<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nitro Performance</title><style>
:root{color-scheme:dark;--bg:#06080b;--panel:#10161d;--panel2:#151d26;--line:#26313d;--text:#edf6ff;--muted:#8ca0b3;--ok:#54d66a;--warn:#f7c948;--hot:#ff6565;--blue:#75a7ff}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:ui-sans-serif,system-ui,Segoe UI,Roboto,Arial;padding:14px}main{max-width:1320px;margin:0 auto}.top{display:flex;justify-content:space-between;gap:12px;align-items:end;margin:6px 0 14px}h1{font-size:24px;margin:0}small,.muted{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:10px}.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px;min-height:100px}.span2{grid-column:span 2}.span3{grid-column:span 3}.span4{grid-column:span 4}.span5{grid-column:span 5}.span6{grid-column:span 6}.span7{grid-column:span 7}.span12{grid-column:1/-1}.label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.value{font-size:30px;font-weight:780;margin:5px 0 3px}.bar{height:8px;background:#080d12;border:1px solid #1e2a35;border-radius:99px;overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,var(--ok),var(--warn),var(--hot));width:0}.mini{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-top:8px}.core{height:24px;background:#0a1016;border:1px solid var(--line);border-radius:5px;position:relative;overflow:hidden}.core b{position:absolute;inset:0;background:#355f49}.core span{position:absolute;inset:4px;font-size:11px}canvas{width:100%;height:180px;background:#080d12;border:1px solid var(--line);border-radius:8px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:10px}table{width:100%;border-collapse:collapse;font-size:13px}td,th{border-top:1px solid var(--line);padding:7px 0;text-align:left}td:last-child,th:last-child{text-align:right;color:var(--muted)}.pill{display:inline-block;background:var(--panel2);border:1px solid var(--line);border-radius:999px;padding:3px 7px;color:var(--muted);font-size:12px;margin:2px 4px 2px 0}.tempgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:8px 0 10px}.temp{background:#0a1016;border:1px solid var(--line);border-radius:8px;padding:10px;min-height:82px}.temp .k{color:var(--muted);font-size:12px}.temp .t{font-size:28px;font-weight:800;margin-top:4px}.temp.ok .t{color:var(--ok)}.temp.warn .t{color:var(--warn)}.temp.hot .t{color:var(--hot)}.temp small{display:block;margin-top:3px}@media(max-width:980px){.grid,.cols{display:block}.card{margin-bottom:10px}.span2,.span3,.span4,.span5,.span6,.span7{grid-column:auto}.mini{grid-template-columns:repeat(2,1fr)}.top{display:block}}
</style></head><body><main><div class="top"><div><h1>Nitro Performance</h1><small id="stamp">coletando...</small></div><small>painel local leve: CPU, GPU, rede, disco, processos e containers</small></div><section class="grid">
<div class="card span3"><div class="label">CPU</div><div class="value" id="cpu">--%</div><div class="bar"><div class="fill" id="cpuBar"></div></div><small id="load"></small><div class="mini" id="cores"></div></div>
<div class="card span3"><div class="label">CPU package</div><div class="value" id="cpuw">-- W</div><div id="freq"></div><small>potencia via Intel RAPL</small></div>
<div class="card span3"><div class="label">GPU</div><div class="value" id="gpu">--%</div><div class="bar"><div class="fill" id="gpuBar"></div></div><small id="gpuMeta"></small></div>
<div class="card span3"><div class="label">NVIDIA power</div><div class="value" id="gpuw">-- W</div><div id="gpuMore"></div></div>
<div class="card span3"><div class="label">Intel iGPU</div><div class="value" id="igpu">--</div><div id="igpuMore"></div></div>
<div class="card span3"><div class="label">RAM</div><div class="value" id="ram">--%</div><div class="bar"><div class="fill" id="ramBar"></div></div><small id="ramtxt"></small></div>
<div class="card span3"><div class="label">Disco</div><div class="value" id="disk">--%</div><div class="bar"><div class="fill" id="diskBar"></div></div><small id="disktxt"></small></div>
<div class="card span3"><div class="label">Rede</div><div class="value" id="net">--</div><small id="nettxt"></small></div>
<div class="card span3"><div class="label">I/O disco</div><div class="value" id="io">--</div><small id="iotxt"></small></div>
<div class="card span12"><div class="label">Historico</div><canvas id="chart" width="1260" height="220"></canvas></div>
<div class="card span12"><div class="label">Temperaturas</div><div class="tempgrid" id="tempCards"></div><canvas id="tempChart" width="1260" height="180"></canvas><table id="temps"></table></div>
<div class="card span6"><div class="label">Processos <a class="pill" href="https://processes.nitro.lan">abrir visao completa</a></div><div class="cols"><table id="procCpu"></table><table id="procMem"></table></div></div>
<div class="card span3"><div class="label">Containers</div><table id="containers"></table></div>
</section></main><script>
const hist=[],tempHist=[];const $=id=>document.getElementById(id);const mb=v=>(v/1024/1024).toFixed(0)+" MB";const gb=v=>(v/1024/1024/1024).toFixed(1)+" GB";const rate=v=>{if(v>1024*1024)return(v/1024/1024).toFixed(1)+" MB/s";if(v>1024)return(v/1024).toFixed(1)+" KB/s";return Math.round(v)+" B/s"};function bar(id,v){$(id).style.width=Math.max(0,Math.min(100,v||0))+"%"}function row(a,b){return`<tr><td>${a}</td><td>${b}</td></tr>`}function draw(){const c=$("chart"),x=c.getContext("2d"),w=c.width,h=c.height;x.clearRect(0,0,w,h);x.strokeStyle="#26313d";for(let i=0;i<=4;i++){x.beginPath();x.moveTo(0,i*h/4);x.lineTo(w,i*h/4);x.stroke()}function line(k,col,scale=100){x.strokeStyle=col;x.lineWidth=3;x.beginPath();hist.forEach((p,i)=>{const xx=i*(w/Math.max(hist.length-1,1));const yy=h-Math.min(100,(p[k]||0)/scale*100)*h/100;i?x.lineTo(xx,yy):x.moveTo(xx,yy)});x.stroke()}line("cpu","#54d66a");line("gpu","#75a7ff");line("ram","#f7c948");line("cpuw","#ff6565",45);x.fillStyle="#8ca0b3";x.fillText("CPU verde | GPU azul | RAM amarelo | CPU watts vermelho",12,18)}function tempClass(v){return v>=85?'hot':v>=70?'warn':'ok'}function tempLine(c,k,col){const x=c.getContext('2d'),w=c.width,h=c.height;x.strokeStyle=col;x.lineWidth=3;x.beginPath();tempHist.forEach((p,i)=>{const xx=i*(w/Math.max(tempHist.length-1,1));const yy=h-Math.min(100,(p[k]||0))*h/100;i?x.lineTo(xx,yy):x.moveTo(xx,yy)});x.stroke()}function drawTemps(){const c=$('tempChart'),x=c.getContext('2d'),w=c.width,h=c.height;x.clearRect(0,0,w,h);x.strokeStyle='#26313d';for(let i=0;i<=4;i++){x.beginPath();x.moveTo(0,i*h/4);x.lineTo(w,i*h/4);x.stroke()}tempLine(c,'cpu','#ff6565');tempLine(c,'nvidia','#75a7ff');tempLine(c,'pch','#f7c948');tempLine(c,'wifi','#54d66a');x.fillStyle='#8ca0b3';x.fillText('CPU vermelho | NVIDIA azul | PCH amarelo | Wi-Fi verde',12,18)}function sensor(d,match){return (d.temps||[]).find(t=>match.some(m=>t.name.toLowerCase().includes(m)))?.c}async function tick(){const d=await(await fetch('/api',{cache:'no-store'})).json();stamp.textContent=new Date(d.time*1000).toLocaleString()+` · host uptime ${Math.round(d.host_uptime_s/3600)}h`;cpu.textContent=d.cpu_percent+"%";bar('cpuBar',d.cpu_percent);load.textContent=`load ${d.load['1m']} / ${d.load['5m']} / ${d.load['15m']}`;cores.innerHTML=(d.cpu_cores||[]).map(c=>`<div class="core"><b style="width:${c.percent}%"></b><span>${c.name}: ${c.percent}%</span></div>`).join('');cpuw.textContent=d.cpu_power_w==null?'n/d':d.cpu_power_w+' W';freq.innerHTML=d.cpu_frequency?`<span class="pill">avg ${d.cpu_frequency.avg_mhz} MHz</span><span class="pill">max ${d.cpu_frequency.max_mhz} MHz</span>`:'<span class="pill">freq n/d</span>';ram.textContent=d.memory.percent+'%';bar('ramBar',d.memory.percent);ramtxt.textContent=`${gb(d.memory.used)} / ${gb(d.memory.total)} · swap ${d.memory.swap_percent}%`;disk.textContent=d.disk.percent+'%';bar('diskBar',d.disk.percent);disktxt.textContent=`${gb(d.disk.used)} / ${gb(d.disk.total)} livres ${gb(d.disk.free)}`;net.textContent=rate(d.network.rx_bps+d.network.tx_bps);nettxt.textContent=`down ${rate(d.network.rx_bps)} · up ${rate(d.network.tx_bps)}`;io.textContent=rate(d.disk_io.read_bps+d.disk_io.write_bps);iotxt.textContent=`read ${rate(d.disk_io.read_bps)} · write ${rate(d.disk_io.write_bps)}`;if(d.gpu){gpu.textContent=d.gpu.util_percent+'%';bar('gpuBar',d.gpu.util_percent);gpuMeta.textContent=`${d.gpu.name} · ${d.gpu.pstate||''} · VRAM ${d.gpu.memory_used_mb}/${d.gpu.memory_total_mb} MB`;gpuw.textContent=(d.gpu.power_w??'--')+' W';gpuMore.innerHTML=`<span class="pill">${d.gpu.temp_c??'--'} C</span><span class="pill">mem util ${d.gpu.memory_util_percent??0}%</span><span class="pill">gfx ${d.gpu.graphics_clock_mhz??'--'} MHz</span><span class="pill">cache ${d.gpu.cached_s??0}s</span>`}if(d.igpu&&d.igpu.available){igpu.textContent=(d.igpu.actual_mhz??d.igpu.current_mhz??'--')+' MHz';igpuMore.innerHTML=`<span class="pill">${d.igpu.name}</span><span class="pill">${d.igpu.rc_state||'rc n/d'}</span><span class="pill">idle ${d.igpu.gpu_idle||'n/d'}</span><span class="pill">max ${d.igpu.max_mhz??'--'} MHz</span>`}else{igpu.textContent='n/d';igpuMore.innerHTML='<span class="pill">debugfs indisponivel</span>'}const cpuTemp=sensor(d,['x86_pkg','package','coretemp']);const pchTemp=sensor(d,['pch']);const wifiTemp=sensor(d,['iwlwifi','wifi']);const nvidiaTemp=d.gpu?.temp_c;const cards=[['CPU package',cpuTemp,'RAPL/package sensor'],['NVIDIA GTX 1650',nvidiaTemp,(d.gpu?.pstate||'')+' '+(d.gpu?.power_w??'--')+' W'],['PCH / chipset',pchTemp,'placa mae/chipset'],['Wi-Fi',wifiTemp,'radio interno']];tempCards.innerHTML=cards.map(([k,v,sub])=>`<div class="temp ${tempClass(v||0)}"><div class="k">${k}</div><div class="t">${v==null?'n/d':v+' C'}</div><small>${sub||''}</small></div>`).join('');temps.innerHTML='<tr><th>Sensor</th><th>Temp</th></tr>'+((d.temps||[]).map(t=>row(t.name,t.c+' C')).join('')||row('sem sensores',''));containers.innerHTML=(d.containers||[]).map(c=>row(c.name,c.status.replace('Up ',''))).join('')||row('sem acesso','');procCpu.innerHTML='<tr><th>CPU</th><th>%</th></tr>'+(d.processes.cpu||[]).map(p=>row(`${p.name} <span class="muted">${p.pid}</span>`,p.cpu_percent)).join('');procMem.innerHTML='<tr><th>RAM</th><th>RSS</th></tr>'+(d.processes.memory||[]).map(p=>row(`${p.name} <span class="muted">${p.pid}</span>`,mb(p.rss))).join('');hist.push({cpu:d.cpu_percent,gpu:d.gpu?.util_percent||0,ram:d.memory.percent,cpuw:d.cpu_power_w||0});tempHist.push({cpu:cpuTemp||0,nvidia:nvidiaTemp||0,pch:pchTemp||0,wifi:wifiTemp||0});while(hist.length>120)hist.shift();while(tempHist.length>120)tempHist.shift();draw();drawTemps()}tick();setInterval(tick,2500);
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        return

<<<<<<< HEAD
    def send_body(self, code, body, content_type, include_body=True):
=======
    def send(self, code, body, content_type):
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
        data = body.encode()
        self.send_response(code)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(data)))
        self.end_headers()
<<<<<<< HEAD
        if include_body:
            self.wfile.write(data)

    def route(self, include_body=True):
        if self.path == "/health":
            self.send_body(200, "ok\n", "text/plain; charset=utf-8", include_body)
        elif self.path in {"/api", "/json"}:
            self.send_body(200, json.dumps(collect(), ensure_ascii=False), "application/json; charset=utf-8", include_body)
        else:
            self.send_body(200, HTML, "text/html; charset=utf-8", include_body)

    def do_HEAD(self):
        self.route(include_body=False)

    def do_GET(self):
        self.route()


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
=======
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self.send(200, "ok\n", "text/plain")
        elif self.path == "/api":
            self.send(200, json.dumps(collect()), "application/json")
        else:
            self.send(200, HTML, "text/html; charset=utf-8")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
>>>>>>> 9a4b7e52047b549a129e43f913666598542107e9
