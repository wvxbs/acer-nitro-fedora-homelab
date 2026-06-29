#!/usr/bin/env python3
import json
import os
import socket
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


DROP_PATH = os.environ.get("FILE_DROP_DIR", "/drop")
SMB_HOST = os.environ.get("FILE_DROP_SMB_HOST", "host.docker.internal")
SMB_PORT = int(os.environ.get("FILE_DROP_SMB_PORT", "445"))
SHARE_NAME = os.environ.get("FILE_DROP_SHARE_NAME", "drop")
TTL_HOURS = os.environ.get("FILE_DROP_TTL_HOURS", "24")
MAX_SIZE = os.environ.get("FILE_DROP_MAX_SIZE", "100G")
IGNORED_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
IGNORED_PREFIXES = ("._",)


def to_bytes(value):
    value = str(value).strip()
    if not value:
        return 0

    suffix = value[-1].upper()
    multipliers = {
        "K": 1024,
        "M": 1024**2,
        "G": 1024**3,
        "T": 1024**4,
    }
    if suffix in multipliers:
        number = float(value[:-1])
        multiplier = multipliers[suffix]
    else:
        number = float(value)
        multiplier = 1
    return int(number * multiplier)


def is_ignored(entry_name):
    return entry_name in IGNORED_NAMES or entry_name.startswith(IGNORED_PREFIXES)


def check_tcp(host, port, timeout=1.2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def directory_stats(path):
    newest = None
    oldest = None
    entries = 0
    bytes_used = 0

    for root, dirs, files in os.walk(path):
        dirs[:] = [name for name in dirs if not is_ignored(name)]
        visible_names = dirs + [name for name in files if not is_ignored(name)]

        if root == path:
            entries = len(visible_names)

        for name in visible_names:
            item_path = os.path.join(root, name)
            try:
                stat = os.stat(item_path, follow_symlinks=False)
            except OSError:
                continue

            modified = stat.st_mtime
            if not os.path.isdir(item_path):
                bytes_used += stat.st_size

            newest = modified if newest is None else max(newest, modified)
            oldest = modified if oldest is None else min(oldest, modified)

    max_bytes = to_bytes(MAX_SIZE)
    free_bytes = max(max_bytes - bytes_used, 0)
    gib = 1024 ** 3
    return {
        "entries": entries,
        "total_gib": round(max_bytes / gib, 1),
        "used_gib": round(bytes_used / gib, 1),
        "free_gib": round(free_bytes / gib, 1),
        "used_bytes": bytes_used,
        "free_bytes": free_bytes,
        "total_bytes": max_bytes,
        "oldest_mtime": oldest,
        "newest_mtime": newest,
    }


def snapshot():
    smb_online = check_tcp(SMB_HOST, SMB_PORT)
    path_ok = os.path.isdir(DROP_PATH) and os.access(DROP_PATH, os.R_OK | os.W_OK)
    stats = directory_stats(DROP_PATH) if os.path.isdir(DROP_PATH) else None
    return {
        "online": smb_online and path_ok,
        "smb_online": smb_online,
        "path_ok": path_ok,
        "share": SHARE_NAME,
        "host": "192.168.15.8",
        "unc": "\\\\192.168.15.8\\drop",
        "uri": "smb://192.168.15.8/drop",
        "access": "guest",
        "ttl_hours": TTL_HOURS,
        "max_size": MAX_SIZE,
        "stats": stats,
        "timestamp": int(time.time()),
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = snapshot()
        if self.path in ("/", "/json"):
            body = json.dumps(data, ensure_ascii=False).encode()
            status = 200
        elif self.path == "/health":
            body = json.dumps(data, ensure_ascii=False).encode()
            status = 200 if data["online"] else 503
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 9838), Handler).serve_forever()
