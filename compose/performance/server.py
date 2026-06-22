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
LAST_CPU = None
LAST_RAPL = None


def read_text(path, default=""):
    try:
        return Path(path).read_text().strip()
    except Exception:
        return default


def cpu_sample():
    global LAST_CPU
    raw = read_text(HOST_PROC / "stat").splitlines()[0].split()[1:]
    vals = [int(v) for v in raw]
    idle = vals[3] + vals[4]
    total = sum(vals)
    if LAST_CPU is None:
        LAST_CPU = (idle, total)
        return 0.0
    last_idle, last_total = LAST_CPU
    LAST_CPU = (idle, total)
    total_delta = max(total - last_total, 1)
    idle_delta = idle - last_idle
    return round((1 - idle_delta / total_delta) * 100, 1)


def mem_sample():
    items = {}
    for line in read_text(HOST_PROC / "meminfo").splitlines():
        key, value = line.split(":", 1)
        items[key] = int(value.strip().split()[0]) * 1024
    total = items.get("MemTotal", 0)
    available = items.get("MemAvailable", 0)
    used = total - available
    return {"total": total, "used": used, "percent": round(used / total * 100, 1) if total else 0}


def load_sample():
    data = read_text(HOST_PROC / "loadavg", "0 0 0").split()
    return {"1m": float(data[0]), "5m": float(data[1]), "15m": float(data[2])}


def uptime_sample():
    up = float(read_text(HOST_PROC / "uptime", "0").split()[0])
    return round(up)


def disk_sample():
    st = os.statvfs("/")
    total = st.f_blocks * st.f_frsize
    free = st.f_bavail * st.f_frsize
    used = total - free
    return {"total": total, "used": used, "percent": round(used / total * 100, 1) if total else 0}


def cpu_power_watts():
    global LAST_RAPL
    readings = []
    for path in HOST_SYS.glob("class/powercap/intel-rapl:*/energy_uj"):
        try:
            name = read_text(path.parent / "name", path.parent.name)
            energy = int(read_text(path))
            readings.append((name, energy))
        except Exception:
            pass
    now = time.time()
    if not readings:
        return None
    total_energy = sum(v for _, v in readings)
    if LAST_RAPL is None:
        LAST_RAPL = (now, total_energy)
        return None
    last_time, last_energy = LAST_RAPL
    LAST_RAPL = (now, total_energy)
    delta_s = max(now - last_time, 0.001)
    delta_uj = total_energy - last_energy
    if delta_uj < 0:
        return None
    return round(delta_uj / delta_s / 1_000_000, 1)


def temps_sample():
    temps = []
    for zone in HOST_SYS.glob("class/thermal/thermal_zone*"):
        temp = read_text(zone / "temp")
        if not temp:
            continue
        label = read_text(zone / "type", zone.name)
        try:
            value = round(int(temp) / 1000, 1)
            if value > 0:
                temps.append({"name": label, "c": value})
        except ValueError:
            pass
    return sorted(temps, key=lambda x: x["c"], reverse=True)[:8]


def safe_float(value):
    try:
        if value in ("", "N/A", "[N/A]"):
            return None
        return float(value)
    except Exception:
        return None


def gpu_sample():
    query = "name,temperature.gpu,power.draw,power.limit,utilization.gpu,memory.used,memory.total"
    cmd = ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"]
    try:
        out = subprocess.check_output(cmd, text=True, timeout=2).strip()
    except Exception:
        return None
    if not out:
        return None
    fields = [x.strip() for x in out.splitlines()[0].split(",")]
    while len(fields) < 7:
        fields.append("")
    return {
        "name": fields[0],
        "temp_c": safe_float(fields[1]),
        "power_w": safe_float(fields[2]),
        "power_limit_w": safe_float(fields[3]),
        "util_percent": safe_float(fields[4]) or 0,
        "memory_used_mb": safe_float(fields[5]) or 0,
        "memory_total_mb": safe_float(fields[6]) or 0,
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


def docker_sample():
    sock_path = "/var/run/docker.sock"
    if not Path(sock_path).exists():
        return []
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(2)
        client.connect(sock_path)
        client.sendall(b"GET /containers/json HTTP/1.1\r\nHost: docker\r\nConnection: close\r\n\r\n")
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
            return []
        if b"transfer-encoding: chunked" in header.lower():
            body = decode_chunked(body)
        containers = json.loads(body.decode())
    except Exception:
        return []
    rows = []
    for item in containers:
        name = (item.get("Names") or [""])[0].lstrip("/")
        rows.append({"name": name, "status": item.get("Status", "")})
    return rows


def collect():
    return {
        "host": socket.gethostname(),
        "time": int(time.time()),
        "app_uptime_s": round(time.time() - STARTED),
        "host_uptime_s": uptime_sample(),
        "cpu_percent": cpu_sample(),
        "cpu_power_w": cpu_power_watts(),
        "load": load_sample(),
        "memory": mem_sample(),
        "disk": disk_sample(),
        "temps": temps_sample(),
        "gpu": gpu_sample(),
        "containers": docker_sample(),
    }


HTML = """<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nitro Performance</title>
<style>
:root{color-scheme:dark;--bg:#080b0f;--panel:#111820;--muted:#8fa1b3;--line:#22303c;--ok:#53d86a;--warn:#f7c948;--hot:#ff6b6b;--text:#eef6ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:ui-sans-serif,system-ui,Segoe UI,Roboto,Arial;padding:18px}
main{max-width:1180px;margin:0 auto}.top{display:flex;justify-content:space-between;gap:14px;align-items:end;margin-bottom:14px}
h1{font-size:24px;margin:0}small,.muted{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px;min-height:112px}.wide{grid-column:span 2}.full{grid-column:1/-1}
.label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.value{font-size:34px;font-weight:750;margin:6px 0 2px}
.bar{height:9px;background:#0b1117;border-radius:99px;overflow:hidden;border:1px solid #1b2731}.fill{height:100%;background:linear-gradient(90deg,var(--ok),var(--warn),var(--hot));width:0}
canvas{width:100%;height:170px;background:#0b1117;border:1px solid var(--line);border-radius:8px}.split{display:grid;grid-template-columns:1fr 1fr;gap:12px}
table{width:100%;border-collapse:collapse}td{border-top:1px solid var(--line);padding:8px 0;color:#d7e3ef}td:last-child{text-align:right;color:var(--muted)}
@media(max-width:900px){.grid,.split{grid-template-columns:1fr}.wide{grid-column:auto}.top{display:block}.value{font-size:30px}}
</style></head><body><main><div class="top"><div><h1>Nitro Performance</h1><small id="stamp">coletando...</small></div><small>CPU + GPU + containers em um painel só</small></div>
<section class="grid">
<div class="card"><div class="label">CPU</div><div class="value" id="cpu">--%</div><div class="bar"><div class="fill" id="cpuBar"></div></div><small id="load"></small></div>
<div class="card"><div class="label">Potência CPU</div><div class="value" id="cpuw">-- W</div><small>via Intel RAPL quando disponível</small></div>
<div class="card"><div class="label">GPU</div><div class="value" id="gpu">--%</div><div class="bar"><div class="fill" id="gpuBar"></div></div><small id="gpuname"></small></div>
<div class="card"><div class="label">Potência GPU</div><div class="value" id="gpuw">-- W</div><small id="gput"></small></div>
<div class="card wide"><div class="label">RAM</div><div class="value" id="ram">--%</div><div class="bar"><div class="fill" id="ramBar"></div></div><small id="ramtxt"></small></div>
<div class="card wide"><div class="label">Disco</div><div class="value" id="disk">--%</div><div class="bar"><div class="fill" id="diskBar"></div></div><small id="disktxt"></small></div>
<div class="card full"><div class="label">Histórico</div><canvas id="chart" width="1100" height="220"></canvas></div>
<div class="card wide"><div class="label">Temperaturas</div><table id="temps"></table></div>
<div class="card wide"><div class="label">Containers ativos</div><table id="containers"></table></div>
</section></main><script>
const hist=[];const mb=v=>(v/1024/1024).toFixed(0)+" MB";const gb=v=>(v/1024/1024/1024).toFixed(1)+" GB";
function setBar(id,v){document.getElementById(id).style.width=Math.max(0,Math.min(100,v))+"%"}
function draw(){const c=document.getElementById("chart"),x=c.getContext("2d"),w=c.width,h=c.height;x.clearRect(0,0,w,h);x.strokeStyle="#22303c";for(let i=0;i<=4;i++){x.beginPath();x.moveTo(0,i*h/4);x.lineTo(w,i*h/4);x.stroke()}function line(k,col){x.strokeStyle=col;x.lineWidth=3;x.beginPath();hist.forEach((p,i)=>{const xx=i*(w/Math.max(hist.length-1,1));const yy=h-(p[k]||0)*h/100;i?x.lineTo(xx,yy):x.moveTo(xx,yy)});x.stroke()}line("cpu","#53d86a");line("gpu","#7aa2ff");line("ram","#f7c948");x.fillStyle="#8fa1b3";x.fillText("CPU verde | GPU azul | RAM amarelo",12,18)}
async function tick(){const r=await fetch("/api");const d=await r.json();stamp.textContent=new Date(d.time*1000).toLocaleString()+" · uptime "+Math.round(d.host_uptime_s/3600)+"h";
cpu.textContent=d.cpu_percent+"%";setBar("cpuBar",d.cpu_percent);load.textContent=`load ${d.load["1m"]} / ${d.load["5m"]} / ${d.load["15m"]}`;
cpuw.textContent=d.cpu_power_w==null?"n/d":d.cpu_power_w+" W";ram.textContent=d.memory.percent+"%";setBar("ramBar",d.memory.percent);ramtxt.textContent=mb(d.memory.used)+" / "+mb(d.memory.total);
disk.textContent=d.disk.percent+"%";setBar("diskBar",d.disk.percent);disktxt.textContent=gb(d.disk.used)+" / "+gb(d.disk.total);
if(d.gpu){gpu.textContent=(d.gpu.util_percent??0)+"%";setBar("gpuBar",d.gpu.util_percent??0);gpuname.textContent=d.gpu.name||"";gpuw.textContent=(d.gpu.power_w??"--")+" W";gput.textContent=(d.gpu.temp_c??"--")+" C · "+(d.gpu.memory_used_mb??0)+"/"+(d.gpu.memory_total_mb??0)+" MB VRAM"}
temps.innerHTML=(d.temps||[]).map(t=>`<tr><td>${t.name}</td><td>${t.c} C</td></tr>`).join("")||"<tr><td>sem sensores</td><td></td></tr>";
containers.innerHTML=(d.containers||[]).map(c=>`<tr><td>${c.name}</td><td>${c.status}</td></tr>`).join("")||"<tr><td>sem acesso</td><td></td></tr>";
hist.push({cpu:d.cpu_percent,gpu:d.gpu?.util_percent||0,ram:d.memory.percent});while(hist.length>80)hist.shift();draw()}
tick();setInterval(tick,3000);
</script></body></html>"""


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
