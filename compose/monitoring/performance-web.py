#!/usr/bin/env python3
import html
import json
import os
import shutil
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


PROC = os.environ.get("NITRO_PROC_PATH", "/host/proc")
ROOT = os.environ.get("NITRO_ROOT_PATH", "/host/root")

_last_cpu = None
_last_net = None


def read_text(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().strip()


def read_cpu():
    global _last_cpu
    fields = read_text(os.path.join(PROC, "stat")).splitlines()[0].split()[1:]
    values = [int(value) for value in fields]
    idle = values[3] + values[4]
    total = sum(values)
    current = (idle, total)

    if _last_cpu is None:
        _last_cpu = current
        return None

    idle_delta = idle - _last_cpu[0]
    total_delta = total - _last_cpu[1]
    _last_cpu = current
    if total_delta <= 0:
        return None
    return round((1 - idle_delta / total_delta) * 100, 1)


def read_mem():
    values = {}
    for line in read_text(os.path.join(PROC, "meminfo")).splitlines():
        key, raw = line.split(":", 1)
        values[key] = int(raw.strip().split()[0])

    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", 0)
    used = max(total - available, 0)
    percent = round((used / total) * 100, 1) if total else None
    return {
        "total_gib": round(total / 1024 / 1024, 1),
        "used_gib": round(used / 1024 / 1024, 1),
        "available_gib": round(available / 1024 / 1024, 1),
        "percent": percent,
    }


def read_load():
    one, five, fifteen, *_ = read_text(os.path.join(PROC, "loadavg")).split()
    return {"one": float(one), "five": float(five), "fifteen": float(fifteen)}


def read_uptime():
    seconds = float(read_text(os.path.join(PROC, "uptime")).split()[0])
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    return {"seconds": int(seconds), "label": f"{days}d {hours}h {minutes}m"}


def read_disk():
    usage = shutil.disk_usage(ROOT)
    percent = round((usage.used / usage.total) * 100, 1) if usage.total else None
    gib = 1024 ** 3
    return {
        "path": ROOT,
        "total_gib": round(usage.total / gib, 1),
        "used_gib": round(usage.used / gib, 1),
        "free_gib": round(usage.free / gib, 1),
        "percent": percent,
    }


def read_net():
    global _last_net
    total_rx = 0
    total_tx = 0
    for line in read_text(os.path.join(PROC, "net/dev")).splitlines()[2:]:
        name, raw = line.split(":", 1)
        if name.strip() == "lo":
            continue
        fields = raw.split()
        total_rx += int(fields[0])
        total_tx += int(fields[8])

    now = time.monotonic()
    current = (now, total_rx, total_tx)
    rates = {"rx_kib_s": None, "tx_kib_s": None}
    if _last_net is not None:
        elapsed = max(now - _last_net[0], 0.001)
        rates = {
            "rx_kib_s": round((total_rx - _last_net[1]) / elapsed / 1024, 1),
            "tx_kib_s": round((total_tx - _last_net[2]) / elapsed / 1024, 1),
        }
    _last_net = current
    return {
        "rx_gib": round(total_rx / 1024 ** 3, 2),
        "tx_gib": round(total_tx / 1024 ** 3, 2),
        **rates,
    }


def read_hostname():
    try:
        return read_text(os.path.join(ROOT, "etc/hostname"))
    except OSError:
        pass
    try:
        return read_text(os.path.join(PROC, "sys/kernel/hostname"))
    except OSError:
        return "nitro"


def snapshot():
    return {
        "hostname": read_hostname(),
        "timestamp": int(time.time()),
        "cpu_percent": read_cpu(),
        "memory": read_mem(),
        "load": read_load(),
        "uptime": read_uptime(),
        "disk": read_disk(),
    }


def percent_bar(value):
    width = 0 if value is None else max(0, min(100, value))
    label = "Indisponivel" if value is None else f"{value}%"
    return f"""
      <div class="bar" aria-label="{html.escape(label)}">
        <span style="width: {width}%"></span>
      </div>
    """


def metric(title, value, detail="", percent=None):
    return f"""
      <section class="metric">
        <dt>{html.escape(title)}</dt>
        <dd>{html.escape(str(value))}</dd>
        <p>{html.escape(detail)}</p>
        {percent_bar(percent) if percent is not None else ""}
      </section>
    """


def render_html(data):
    cpu = "Amostrando" if data["cpu_percent"] is None else f"{data['cpu_percent']}%"
    mem = data["memory"]
    load = data["load"]
    uptime = data["uptime"]
    disk = data["disk"]

    cards = [
        metric("CPU", cpu, "Uso agregado do host", data["cpu_percent"]),
        metric(
            "Memoria",
            f"{mem['used_gib']} / {mem['total_gib']} GiB",
            f"{mem['available_gib']} GiB disponiveis",
            mem["percent"],
        ),
        metric("Carga", f"{load['one']} / {load['five']} / {load['fifteen']}", "1, 5 e 15 minutos"),
        metric("Uptime", uptime["label"], f"{uptime['seconds']} segundos"),
        metric(
            "Disco",
            f"{disk['used_gib']} / {disk['total_gib']} GiB",
            f"{disk['free_gib']} GiB livres",
            disk["percent"],
        ),
    ]

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="4">
  <title>Nitro Performance</title>
  <style>
    :root {{
      color-scheme: light dark;
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --bg: #f5f7fa;
      --surface: #ffffff;
      --surface-2: #eef2f6;
      --text: #17202a;
      --muted: #5b6877;
      --line: #d6dee8;
      --accent: #0f6cbd;
      --shadow: 0 12px 30px rgb(20 32 45 / 8%);
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #101216;
        --surface: #191d23;
        --surface-2: #222832;
        --text: #f4f7fb;
        --muted: #a9b4c2;
        --line: #303946;
        --accent: #72bfff;
        --shadow: 0 14px 34px rgb(0 0 0 / 28%);
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; background: var(--bg); color: var(--text); }}
    main {{ width: min(1040px, 100%); margin: 0 auto; padding: 28px 18px 36px; }}
    header {{ display: flex; align-items: flex-end; justify-content: space-between; gap: 14px; margin-bottom: 18px; border-bottom: 1px solid var(--line); padding-bottom: 18px; }}
    h1 {{ margin: 0; font-size: clamp(1.8rem, 5vw, 3rem); line-height: 1; letter-spacing: 0; }}
    .subtitle {{ margin: 8px 0 0; color: var(--muted); }}
    a.button {{ display: inline-flex; min-height: 42px; align-items: center; justify-content: center; border: 1px solid var(--line); border-radius: 8px; padding: 0 14px; background: var(--surface-2); color: var(--text); font-weight: 650; text-decoration: none; }}
    a.button:hover, a.button:focus {{ border-color: var(--accent); outline: 2px solid transparent; }}
    dl {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; margin: 0; }}
    .metric {{ display: grid; gap: 8px; min-height: 150px; border: 1px solid var(--line); border-radius: 8px; padding: 16px; background: var(--surface); box-shadow: var(--shadow); }}
    dt {{ color: var(--muted); font-size: 13px; }}
    dd {{ margin: 0; font-size: 1.55rem; font-weight: 760; overflow-wrap: anywhere; }}
    p {{ margin: 0; color: var(--muted); }}
    .bar {{ height: 9px; border-radius: 999px; background: var(--surface-2); overflow: hidden; border: 1px solid var(--line); }}
    .bar span {{ display: block; height: 100%; background: var(--accent); }}
    .foot {{ margin-top: 18px; color: var(--muted); }}
    code {{ color: var(--accent); }}
    @media (max-width: 620px) {{
      header {{ display: block; }}
      a.button {{ width: 100%; margin-top: 16px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Nitro Performance</h1>
        <p class="subtitle">Leituras diretas do host {html.escape(data['hostname'])}, atualizadas a cada 4 segundos.</p>
      </div>
      <a class="button" href="https://nitro.lan">Homelab</a>
    </header>
    <dl>
      {''.join(cards)}
    </dl>
    <p class="foot">JSON em <code>/json</code>. Glances continua separado em <code>https://glances.nitro.lan</code>.</p>
  </main>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data = snapshot()
            if self.path == "/json":
                body = json.dumps(data, ensure_ascii=False).encode()
                content_type = "application/json; charset=utf-8"
            elif self.path in ("/", "/health"):
                body = render_html(data).encode()
                content_type = "text/html; charset=utf-8"
            else:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            body = str(exc).encode()
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 9837), Handler).serve_forever()
