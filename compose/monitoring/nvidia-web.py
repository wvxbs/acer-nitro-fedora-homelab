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
        dict(zip(QUERY, [cell.strip() for cell in row]))
        for row in csv.reader(output.splitlines())
    ]


def render_html(gpus):
    cards = []
    for gpu in gpus:
        name = html.escape(gpu.get("name", "GPU"))
        util = html.escape(gpu.get("utilization.gpu", "?"))
        used = html.escape(gpu.get("memory.used", "?"))
        total = html.escape(gpu.get("memory.total", "?"))
        temp = html.escape(gpu.get("temperature.gpu", "?"))
        power = html.escape(gpu.get("power.draw", "?"))
        limit = html.escape(gpu.get("power.limit", "?"))
        driver = html.escape(gpu.get("driver_version", "?"))
        cards.append(
            f"""
            <section>
              <h2>{name}</h2>
              <dl>
                <div><dt>GPU</dt><dd>{util}%</dd></div>
                <div><dt>VRAM</dt><dd>{used} / {total} MiB</dd></div>
                <div><dt>Temp</dt><dd>{temp} C</dd></div>
                <div><dt>Power</dt><dd>{power} / {limit} W</dd></div>
                <div><dt>Driver</dt><dd>{driver}</dd></div>
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
    :root {{ color-scheme: dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 0; background: #101114; color: #f4f4f5; }}
    main {{ max-width: 760px; margin: 0 auto; padding: 24px; }}
    h1 {{ margin: 0 0 16px; font-size: 28px; }}
    section {{ border: 1px solid #2f3037; border-radius: 8px; padding: 18px; background: #181a1f; }}
    h2 {{ margin: 0 0 16px; font-size: 20px; }}
    dl {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin: 0; }}
    div {{ padding: 12px; border-radius: 6px; background: #22242b; }}
    dt {{ color: #a1a1aa; font-size: 13px; }}
    dd {{ margin: 4px 0 0; font-size: 20px; font-weight: 700; }}
    p {{ color: #a1a1aa; }}
  </style>
</head>
<body>
  <main>
    <h1>Nitro GPU</h1>
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
