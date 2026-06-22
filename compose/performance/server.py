#!/usr/bin/env python3
import json
import os
import socket
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST_PROC = Path(os.getenv("HOST_PROC", "/host/proc"))
HOST_SYS = Path(os.getenv("HOST_SYS", "/host/sys"))
PORT = int(os.getenv("PORT", "9837"))
STARTED = time.time()
HZ = os.sysconf(os.sysconf_names.get("SC_CLK_TCK", "SC_CLK_TCK")) if hasattr(os, "sysconf") else 100
LAST_CPU = None
LAST_RAPL = None
LAST_NET = None
LAST_DISK = None
LAST_PROC = {}


def read_text(path, default=""):
    try:
        return Path(path).read_text().strip()
    except Exception:
        return default


def pct(part, total):
    return round(part / total * 100, 1) if total else 0


def fmt_bytes(value):
    value = float(value or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024


def cpu_snapshot():
    rows = []
    for line in read_text(HOST_PROC / "stat").splitlines():
        if not line.startswith("cpu"):
            continue
        parts = line.split()
        name = parts[0]
        vals = [int(v) for v in parts[1:]]
        idle = vals[3] + vals[4]
        total = sum(vals)
        rows.append((name, idle, total))
    return rows


def cpu_sample():
    global LAST_CPU
    now = cpu_snapshot()
    if LAST_CPU is None:
        LAST_CPU = now
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
        if name == "cpu":
            total_percent = value
        else:
            cores.append({"name": name.replace("cpu", ""), "percent": value})
    return {"total": total_percent, "cores": cores}


def cpu_freq_sample():
    freqs = []
    for path in sorted(HOST_SYS.glob("devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq")):
        try:
            freqs.append(int(read_text(path)) / 1000)
        except Exception:
            pass
    if not freqs:
        return None
    return {"avg_mhz": round(sum(freqs) / len(freqs)), "max_mhz": round(max(freqs)), "min_mhz": round(min(freqs))}


def mem_sample():
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
    data = read_text(HOST_PROC / "loadavg", "0 0 0").split()
    return {"1m": float(data[0]), "5m": float(data[1]), "15m": float(data[2])}


def uptime_sample():
    return round(float(read_text(HOST_PROC / "uptime", "0").split()[0]))


def disk_sample():
    st = os.statvfs("/")
    total = st.f_blocks * st.f_frsize
    free = st.f_bavail * st.f_frsize
    used = total - free
    return {"total": total, "used": used, "free": free, "percent": pct(used, total)}


def disk_io_snapshot():
    devices = {}
    for line in read_text(HOST_PROC / "diskstats").splitlines():
        parts = line.split()
        if len(parts) < 14:
            continue
        name = parts[2]
        if name.startswith(("loop", "ram", "zram")):
            continue
        if any(name.endswith(str(i)) for i in range(10)) and not name.startswith("nvme"):
            continue
        read_sectors = int(parts[5])
        write_sectors = int(parts[9])
        devices[name] = {"read_bytes": read_sectors * 512, "write_bytes": write_sectors * 512}
    return devices


def disk_io_sample():
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
    for name, item in now.items():
        prev = last.get(name, item)
        rb = max(item["read_bytes"] - prev["read_bytes"], 0) / dt
        wb = max(item["write_bytes"] - prev["write_bytes"], 0) / dt
        read_total += rb
        write_total += wb
        if rb or wb:
            devices.append({"name": name, "read_bps": round(rb), "write_bps": round(wb)})
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


def net_sample():
    global LAST_NET
    now_time = time.time()
    now = net_snapshot()
    if LAST_NET is None:
        LAST_NET = (now_time, now)
        return {"rx_bps": 0, "tx_bps": 0, "interfaces": []}
    last_time, last = LAST_NET
    LAST_NET = (now_time, now)
    dt = max(now_time - last_time, 0.001)
    rx_total = tx_total = 0
    interfaces = []
    for iface, item in now.items():
        prev = last.get(iface, item)
        rx = max(item["rx"] - prev["rx"], 0) / dt
        tx = max(item["tx"] - prev["tx"], 0) / dt
        rx_total += rx
        tx_total += tx
        interfaces.append({"name": iface, "rx_bps": round(rx), "tx_bps": round(tx)})
    interfaces.sort(key=lambda i: i["rx_bps"] + i["tx_bps"], reverse=True)
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


def gpu_sample():
    query = "name,temperature.gpu,power.draw,power.limit,utilization.gpu,utilization.memory,memory.used,memory.total,clocks.current.graphics,clocks.current.memory"
    cmd = ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"]
    try:
        out = subprocess.check_output(cmd, text=True, timeout=2).strip()
    except Exception:
        return None
    fields = [x.strip() for x in out.splitlines()[0].split(",")]
    while len(fields) < 10:
        fields.append("")
    return {
        "name": fields[0],
        "temp_c": safe_float(fields[1]),
        "power_w": safe_float(fields[2]),
        "power_limit_w": safe_float(fields[3]),
        "util_percent": safe_float(fields[4]) or 0,
        "memory_util_percent": safe_float(fields[5]) or 0,
        "memory_used_mb": safe_float(fields[6]) or 0,
        "memory_total_mb": safe_float(fields[7]) or 0,
        "graphics_clock_mhz": safe_float(fields[8]),
        "memory_clock_mhz": safe_float(fields[9]),
    }


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
        name = (item.get("Names") or [""])[0].lstrip("/")
        rows.append({"name": name, "image": item.get("Image", ""), "status": item.get("Status", "")})
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
            rss_pages = int(rest[21])
            rss = rss_pages * os.sysconf("SC_PAGE_SIZE")
            current[pid] = (now, ticks)
            prev = LAST_PROC.get(pid)
            cpu = 0.0
            if prev:
                last_time, last_ticks = prev
                cpu = max(ticks - last_ticks, 0) / HZ / max(now - last_time, 0.001) * 100
            rows.append({"pid": pid, "name": comm[:32], "cpu_percent": round(cpu, 1), "rss": rss})
        except Exception:
            pass
    LAST_PROC = current
    by_cpu = sorted(rows, key=lambda r: r["cpu_percent"], reverse=True)[:8]
    by_mem = sorted(rows, key=lambda r: r["rss"], reverse=True)[:8]
    return {"cpu": by_cpu, "memory": by_mem}


def collect():
    cpu = cpu_sample()
    return {
        "host": socket.gethostname(),
        "time": int(time.time()),
        "app_uptime_s": round(time.time() - STARTED),
        "host_uptime_s": uptime_sample(),
        "cpu_percent": cpu["total"],
        "cpu_cores": cpu["cores"],
        "cpu_frequency": cpu_freq_sample(),
        "cpu_power_w": cpu_power_watts(),
        "load": load_sample(),
        "memory": mem_sample(),
        "disk": disk_sample(),
        "disk_io": disk_io_sample(),
        "network": net_sample(),
        "temps": temps_sample(),
        "gpu": gpu_sample(),
        "containers": docker_sample(),
        "processes": processes_sample(),
    }


HTML = r'''<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nitro Performance</title><style>
:root{color-scheme:dark;--bg:#06080b;--panel:#10161d;--panel2:#151d26;--line:#26313d;--text:#edf6ff;--muted:#8ca0b3;--ok:#54d66a;--warn:#f7c948;--hot:#ff6565;--blue:#75a7ff}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:ui-sans-serif,system-ui,Segoe UI,Roboto,Arial;padding:14px}main{max-width:1320px;margin:0 auto}.top{display:flex;justify-content:space-between;gap:12px;align-items:end;margin:6px 0 14px}h1{font-size:24px;margin:0}small,.muted{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:10px}.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px;min-height:100px}.span2{grid-column:span 2}.span3{grid-column:span 3}.span4{grid-column:span 4}.span5{grid-column:span 5}.span6{grid-column:span 6}.span7{grid-column:span 7}.span12{grid-column:1/-1}.label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.value{font-size:30px;font-weight:780;margin:5px 0 3px}.bar{height:8px;background:#080d12;border:1px solid #1e2a35;border-radius:99px;overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,var(--ok),var(--warn),var(--hot));width:0}.mini{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-top:8px}.core{height:24px;background:#0a1016;border:1px solid var(--line);border-radius:5px;position:relative;overflow:hidden}.core b{position:absolute;inset:0;background:#355f49}.core span{position:absolute;inset:4px;font-size:11px}canvas{width:100%;height:180px;background:#080d12;border:1px solid var(--line);border-radius:8px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:10px}table{width:100%;border-collapse:collapse;font-size:13px}td,th{border-top:1px solid var(--line);padding:7px 0;text-align:left}td:last-child,th:last-child{text-align:right;color:var(--muted)}.pill{display:inline-block;background:var(--panel2);border:1px solid var(--line);border-radius:999px;padding:3px 7px;color:var(--muted);font-size:12px;margin:2px 4px 2px 0}@media(max-width:980px){.grid,.cols{display:block}.card{margin-bottom:10px}.span2,.span3,.span4,.span5,.span6,.span7{grid-column:auto}.mini{grid-template-columns:repeat(2,1fr)}.top{display:block}}
</style></head><body><main><div class="top"><div><h1>Nitro Performance</h1><small id="stamp">coletando...</small></div><small>painel local leve: CPU, GPU, rede, disco, processos e containers</small></div><section class="grid">
<div class="card span3"><div class="label">CPU</div><div class="value" id="cpu">--%</div><div class="bar"><div class="fill" id="cpuBar"></div></div><small id="load"></small><div class="mini" id="cores"></div></div>
<div class="card span3"><div class="label">CPU package</div><div class="value" id="cpuw">-- W</div><div id="freq"></div><small>potencia via Intel RAPL</small></div>
<div class="card span3"><div class="label">GPU</div><div class="value" id="gpu">--%</div><div class="bar"><div class="fill" id="gpuBar"></div></div><small id="gpuMeta"></small></div>
<div class="card span3"><div class="label">GPU power</div><div class="value" id="gpuw">-- W</div><div id="gpuMore"></div></div>
<div class="card span3"><div class="label">RAM</div><div class="value" id="ram">--%</div><div class="bar"><div class="fill" id="ramBar"></div></div><small id="ramtxt"></small></div>
<div class="card span3"><div class="label">Disco</div><div class="value" id="disk">--%</div><div class="bar"><div class="fill" id="diskBar"></div></div><small id="disktxt"></small></div>
<div class="card span3"><div class="label">Rede</div><div class="value" id="net">--</div><small id="nettxt"></small></div>
<div class="card span3"><div class="label">I/O disco</div><div class="value" id="io">--</div><small id="iotxt"></small></div>
<div class="card span12"><div class="label">Historico</div><canvas id="chart" width="1260" height="220"></canvas></div>
<div class="card span6"><div class="label">Processos</div><div class="cols"><table id="procCpu"></table><table id="procMem"></table></div></div>
<div class="card span3"><div class="label">Temperaturas</div><table id="temps"></table></div>
<div class="card span3"><div class="label">Containers</div><table id="containers"></table></div>
</section></main><script>
const hist=[];const $=id=>document.getElementById(id);const mb=v=>(v/1024/1024).toFixed(0)+" MB";const gb=v=>(v/1024/1024/1024).toFixed(1)+" GB";const rate=v=>{if(v>1024*1024)return(v/1024/1024).toFixed(1)+" MB/s";if(v>1024)return(v/1024).toFixed(1)+" KB/s";return Math.round(v)+" B/s"};function bar(id,v){$(id).style.width=Math.max(0,Math.min(100,v||0))+"%"}function row(a,b){return`<tr><td>${a}</td><td>${b}</td></tr>`}function draw(){const c=$("chart"),x=c.getContext("2d"),w=c.width,h=c.height;x.clearRect(0,0,w,h);x.strokeStyle="#26313d";for(let i=0;i<=4;i++){x.beginPath();x.moveTo(0,i*h/4);x.lineTo(w,i*h/4);x.stroke()}function line(k,col,scale=100){x.strokeStyle=col;x.lineWidth=3;x.beginPath();hist.forEach((p,i)=>{const xx=i*(w/Math.max(hist.length-1,1));const yy=h-Math.min(100,(p[k]||0)/scale*100)*h/100;i?x.lineTo(xx,yy):x.moveTo(xx,yy)});x.stroke()}line("cpu","#54d66a");line("gpu","#75a7ff");line("ram","#f7c948");line("cpuw","#ff6565",45);x.fillStyle="#8ca0b3";x.fillText("CPU verde | GPU azul | RAM amarelo | CPU watts vermelho",12,18)}async function tick(){const d=await(await fetch('/api',{cache:'no-store'})).json();stamp.textContent=new Date(d.time*1000).toLocaleString()+` · host uptime ${Math.round(d.host_uptime_s/3600)}h`;cpu.textContent=d.cpu_percent+"%";bar('cpuBar',d.cpu_percent);load.textContent=`load ${d.load['1m']} / ${d.load['5m']} / ${d.load['15m']}`;cores.innerHTML=(d.cpu_cores||[]).map(c=>`<div class="core"><b style="width:${c.percent}%"></b><span>${c.name}: ${c.percent}%</span></div>`).join('');cpuw.textContent=d.cpu_power_w==null?'n/d':d.cpu_power_w+' W';freq.innerHTML=d.cpu_frequency?`<span class="pill">avg ${d.cpu_frequency.avg_mhz} MHz</span><span class="pill">max ${d.cpu_frequency.max_mhz} MHz</span>`:'<span class="pill">freq n/d</span>';ram.textContent=d.memory.percent+'%';bar('ramBar',d.memory.percent);ramtxt.textContent=`${gb(d.memory.used)} / ${gb(d.memory.total)} · swap ${d.memory.swap_percent}%`;disk.textContent=d.disk.percent+'%';bar('diskBar',d.disk.percent);disktxt.textContent=`${gb(d.disk.used)} / ${gb(d.disk.total)} livres ${gb(d.disk.free)}`;net.textContent=rate(d.network.rx_bps+d.network.tx_bps);nettxt.textContent=`down ${rate(d.network.rx_bps)} · up ${rate(d.network.tx_bps)}`;io.textContent=rate(d.disk_io.read_bps+d.disk_io.write_bps);iotxt.textContent=`read ${rate(d.disk_io.read_bps)} · write ${rate(d.disk_io.write_bps)}`;if(d.gpu){gpu.textContent=d.gpu.util_percent+'%';bar('gpuBar',d.gpu.util_percent);gpuMeta.textContent=`${d.gpu.name} · VRAM ${d.gpu.memory_used_mb}/${d.gpu.memory_total_mb} MB`;gpuw.textContent=(d.gpu.power_w??'--')+' W';gpuMore.innerHTML=`<span class="pill">${d.gpu.temp_c??'--'} C</span><span class="pill">mem util ${d.gpu.memory_util_percent??0}%</span><span class="pill">gfx ${d.gpu.graphics_clock_mhz??'--'} MHz</span><span class="pill">mem ${d.gpu.memory_clock_mhz??'--'} MHz</span>`}temps.innerHTML=(d.temps||[]).map(t=>row(t.name,t.c+' C')).join('')||row('sem sensores','');containers.innerHTML=(d.containers||[]).map(c=>row(c.name,c.status.replace('Up ',''))).join('')||row('sem acesso','');procCpu.innerHTML='<tr><th>CPU</th><th>%</th></tr>'+(d.processes.cpu||[]).map(p=>row(`${p.name} <span class="muted">${p.pid}</span>`,p.cpu_percent)).join('');procMem.innerHTML='<tr><th>RAM</th><th>RSS</th></tr>'+(d.processes.memory||[]).map(p=>row(`${p.name} <span class="muted">${p.pid}</span>`,mb(p.rss))).join('');hist.push({cpu:d.cpu_percent,gpu:d.gpu?.util_percent||0,ram:d.memory.percent,cpuw:d.cpu_power_w||0});while(hist.length>120)hist.shift();draw()}tick();setInterval(tick,2500);
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        return

    def send(self, code, body, content_type):
        data = body.encode()
        self.send_response(code)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(data)))
        self.end_headers()
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