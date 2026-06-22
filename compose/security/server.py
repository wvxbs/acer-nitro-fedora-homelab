#!/usr/bin/env python3
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

DATA_DIR = Path(os.environ.get("SECURITY_DATA_DIR", "/data"))
EVENTS = DATA_DIR / "events.jsonl"
CAPTURES = DATA_DIR / "captures"
HOST = "0.0.0.0"
PORT = int(os.environ.get("SECURITY_PORT", "9838"))


def read_events(limit=250):
    if not EVENTS.exists():
        return []
    lines = EVENTS.read_text(encoding="utf-8", errors="replace").splitlines()
    items = []
    for line in lines[-limit:]:
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(items))


def summarize(events):
    now = time.time()
    last_day = [e for e in events if now - float(e.get("ts", 0)) <= 86400]
    last_hour = [e for e in events if now - float(e.get("ts", 0)) <= 3600]
    by_kind = {}
    for event in last_day:
        kind = event.get("kind", "unknown")
        by_kind[kind] = by_kind.get(kind, 0) + 1
    return {
        "last_hour": len(last_hour),
        "last_day": len(last_day),
        "tty_failures": sum(1 for e in last_day if e.get("kind") == "tty_login_failure"),
        "captures": sum(1 for e in last_day if e.get("capture")),
        "by_kind": by_kind,
    }


def list_captures():
    if not CAPTURES.exists():
        return []
    items = []
    for path in sorted(CAPTURES.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)[:80]:
        if path.is_file():
            items.append({
                "name": path.name,
                "size": path.stat().st_size,
                "mtime": path.stat().st_mtime,
                "url": "/captures/" + path.name,
            })
    return items


def api_payload():
    events = read_events()
    return {
        "time": time.time(),
        "summary": summarize(events),
        "events": events[:120],
        "captures": list_captures(),
    }


HTML = r'''<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nitro Security</title><style>
:root{color-scheme:dark;--bg:#080b0e;--panel:#111820;--panel2:#18212b;--line:#2b3744;--text:#f4f8fb;--muted:#9aaaae;--ok:#56d37b;--warn:#f0c85a;--bad:#ff6b6b;--blue:#79b7ff}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:ui-sans-serif,system-ui,Segoe UI,Roboto,Arial;padding:16px}main{max-width:1220px;margin:0 auto}.top{display:flex;justify-content:space-between;align-items:end;gap:12px;margin:6px 0 14px}h1{margin:0;font-size:26px}.muted,small{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:10px}.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:13px}.span3{grid-column:span 3}.span4{grid-column:span 4}.span8{grid-column:span 8}.span12{grid-column:1/-1}.label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.value{font-size:34px;font-weight:800;margin-top:4px}.pill{display:inline-flex;background:var(--panel2);border:1px solid var(--line);border-radius:999px;padding:4px 8px;margin:3px 5px 3px 0;color:var(--muted);font-size:12px}table{width:100%;border-collapse:collapse;font-size:13px}td,th{border-top:1px solid var(--line);padding:8px 6px;text-align:left;vertical-align:top}td:last-child,th:last-child{text-align:right}.kind{color:var(--blue);font-weight:700}.sev-low{color:var(--ok)}.sev-medium{color:var(--warn)}.sev-high{color:var(--bad)}a{color:var(--blue)}code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;color:#d8e9ff}.note{line-height:1.45}.empty{padding:22px;color:var(--muted);text-align:center;border:1px dashed var(--line);border-radius:8px}@media(max-width:900px){.grid,.top{display:block}.card{margin-bottom:10px}.span3,.span4,.span8{grid-column:auto}td,th{font-size:12px;padding:7px 4px}.hide-mobile{display:none}}
</style></head><body><main><div class="top"><div><h1>Nitro Security</h1><small id="stamp">coletando...</small></div><small>eventos locais, falhas de login e capturas TTY com retencao curta</small></div><section class="grid">
<div class="card span3"><div class="label">Eventos na ultima hora</div><div class="value" id="lastHour">--</div></div>
<div class="card span3"><div class="label">Eventos em 24h</div><div class="value" id="lastDay">--</div></div>
<div class="card span3"><div class="label">Falhas TTY em 24h</div><div class="value" id="ttyFailures">--</div></div>
<div class="card span3"><div class="label">Capturas em 24h</div><div class="value" id="captureCount">--</div></div>
<div class="card span4"><div class="label">Tipos vistos em 24h</div><div id="kinds"></div></div>
<div class="card span8"><div class="label">Politica ativa</div><p class="note">Captura de webcam/audio e limitada a falhas do login fisico local do Fedora, isto e, eventos do processo <code>login</code> em TTY/getty. Falhas de Cockpit, SSH, sudo e outros servicos entram no painel como log, mas nao disparam camera nem microfone.</p></div>
<div class="card span12"><div class="label">Eventos recentes</div><table id="events"></table></div>
<div class="card span12"><div class="label">Capturas recentes</div><table id="captures"></table></div>
</section></main><script>
const $=id=>document.getElementById(id);const fmt=t=>new Date(t*1000).toLocaleString();const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));function sev(s){return s==='high'?'sev-high':s==='medium'?'sev-medium':'sev-low'}function bytes(n){if(!n)return'0 B';if(n>1024*1024)return(n/1024/1024).toFixed(1)+' MB';if(n>1024)return(n/1024).toFixed(1)+' KB';return n+' B'}async function tick(){const d=await(await fetch('/api',{cache:'no-store'})).json();stamp.textContent='Atualizado '+fmt(d.time);lastHour.textContent=d.summary.last_hour;lastDay.textContent=d.summary.last_day;ttyFailures.textContent=d.summary.tty_failures;captureCount.textContent=d.summary.captures;kinds.innerHTML=Object.entries(d.summary.by_kind).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`<span class="pill">${esc(k)}: ${v}</span>`).join('')||'<div class="empty">sem eventos</div>';events.innerHTML='<tr><th>Quando</th><th>Tipo</th><th class="hide-mobile">Origem</th><th>Mensagem</th><th>Sev.</th></tr>'+d.events.map(e=>`<tr><td>${fmt(e.ts)}</td><td class="kind">${esc(e.kind)}</td><td class="hide-mobile">${esc(e.source||'')}</td><td>${esc(e.message||'')}</td><td class="${sev(e.severity)}">${esc(e.severity||'low')}</td></tr>`).join('');if(!d.events.length)events.innerHTML='<tr><td><div class="empty">sem eventos registrados ainda</div></td></tr>';captures.innerHTML='<tr><th>Arquivo</th><th class="hide-mobile">Criado</th><th>Tamanho</th></tr>'+d.captures.map(c=>`<tr><td><a href="${c.url}">${esc(c.name)}</a></td><td class="hide-mobile">${fmt(c.mtime)}</td><td>${bytes(c.size)}</td></tr>`).join('');if(!d.captures.length)captures.innerHTML='<tr><td><div class="empty">nenhuma captura recente</div></td></tr>'}tick();setInterval(tick,5000);
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def send(self, code, body, content_type="text/plain; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = unquote(self.path.split("?", 1)[0])
        if path == "/health":
            self.send(200, "ok\n")
        elif path == "/api":
            self.send(200, json.dumps(api_payload(), ensure_ascii=False), "application/json; charset=utf-8")
        elif path.startswith("/captures/"):
            name = Path(path).name
            file_path = CAPTURES / name
            if not file_path.is_file() or file_path.parent != CAPTURES:
                self.send(404, "not found\n")
                return
            content_type = "video/mp4" if file_path.suffix == ".mp4" else "audio/wav" if file_path.suffix == ".wav" else "application/octet-stream"
            self.send(200, file_path.read_bytes(), content_type)
        else:
            self.send(200, HTML, "text/html; charset=utf-8")


if __name__ == "__main__":
    CAPTURES.mkdir(parents=True, exist_ok=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
