#!/usr/bin/env python3
import csv
import html
import json
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


QUERY = [
    "name",
    "driver_version",
    "utilization.gpu",
    "memory.used",
    "memory.total",
    "temperature.gpu",
    "power.draw",
    "power.limit",
]


def read_gpu():
    cmd = [
        "nvidia-smi",
        f"--query-gpu={','.join(QUERY)}",
        "--format=csv,noheader,nounits",
    ]
    output = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    return [
        dict(zip(QUERY, [normalize(cell) for cell in row]))
        for row in csv.reader(output.splitlines())
    ]


def normalize(value):
    value = value.strip()
    if not value or value.upper() in {"N/A", "[N/A]", "NOT SUPPORTED"}:
        return None
    return value


def text(value, fallback="Indisponivel"):
    return fallback if value is None else html.escape(str(value))


def metric(value, unit="", fallback="Indisponivel"):
    if value is None:
        return fallback
    return f"{html.escape(str(value))}{unit}"


def render_html(gpus):
    cards = []
    for gpu in gpus:
        name = text(gpu.get("name"), "GPU")
        util = metric(gpu.get("utilization.gpu"), "%")
        used = text(gpu.get("memory.used"))
        total = text(gpu.get("memory.total"))
        temp = metric(gpu.get("temperature.gpu"), " C")
        power = metric(gpu.get("power.draw"), " W")
        limit = metric(gpu.get("power.limit"), " W")
        driver = text(gpu.get("driver_version"))
        cards.append(
            f"""
            <section>
              <h2>{name}</h2>
              <dl>
                <div class="metric"><dt>GPU</dt><dd>{util}</dd></div>
                <div class="metric"><dt>VRAM</dt><dd>{used} / {total} MiB</dd></div>
                <div class="metric"><dt>Temp</dt><dd>{temp}</dd></div>
                <div class="metric"><dt>Power draw</dt><dd>{power}</dd></div>
                <div class="metric"><dt>Power limit</dt><dd>{limit}</dd></div>
                <div class="metric"><dt>Driver</dt><dd>{driver}</dd></div>
              </dl>
            </section>
            """
        )
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="5">
  <title>Nitro GPU</title>
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
    main {{ max-width: 860px; margin: 0 auto; padding: 28px 18px 36px; }}
    header {{ display: flex; align-items: flex-end; justify-content: space-between; gap: 14px; margin-bottom: 18px; border-bottom: 1px solid var(--line); padding-bottom: 18px; }}
    h1 {{ margin: 0; font-size: clamp(1.8rem, 5vw, 3rem); line-height: 1; letter-spacing: 0; }}
    .subtitle {{ margin: 8px 0 0; color: var(--muted); }}
    a.button {{ display: inline-flex; min-height: 42px; align-items: center; justify-content: center; border: 1px solid var(--line); border-radius: 8px; padding: 0 14px; background: var(--surface-2); color: var(--text); font-weight: 650; text-decoration: none; }}
    a.button:hover, a.button:focus {{ border-color: var(--accent); outline: 2px solid transparent; }}
    section {{ border: 1px solid var(--line); border-radius: 8px; padding: 18px; background: var(--surface); box-shadow: var(--shadow); }}
    h2 {{ margin: 0 0 16px; font-size: 20px; }}
    dl {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin: 0; }}
    div.metric {{ padding: 12px; border-radius: 8px; background: var(--surface-2); border: 1px solid var(--line); }}
    dt {{ color: var(--muted); font-size: 13px; }}
    dd {{ margin: 4px 0 0; font-size: 20px; font-weight: 750; }}
    p {{ color: var(--muted); }}
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
        <h1>Nitro GPU</h1>
        <p class="subtitle">Leituras locais via nvidia-smi, atualizadas a cada 5 segundos.</p>
      </div>
      <a class="button" href="https://nitro.lan">Homelab</a>
    </header>
    {''.join(cards)}
    <p>Atualiza automaticamente a cada 5 segundos. JSON em <code>/json</code>.</p>
  </main>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            gpus = read_gpu()
            if self.path == "/json":
                body = json.dumps({"gpus": gpus}, ensure_ascii=False).encode()
                content_type = "application/json; charset=utf-8"
            elif self.path in ("/", "/health"):
                body = render_html(gpus).encode()
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
    ThreadingHTTPServer(("0.0.0.0", 9836), Handler).serve_forever()
