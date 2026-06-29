#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

SECURITY_DATA_DIR="${SECURITY_DATA_DIR:-$APPDATA_DIR/security}"
SECURITY_CAPTURE_SECONDS="${SECURITY_CAPTURE_SECONDS:-8}"
SECURITY_RETENTION_DAYS="${SECURITY_RETENTION_DAYS:-7}"

log "Installing local security monitor"

dnf_install ffmpeg v4l-utils alsa-utils || warn "Could not install optional capture packages. The monitor will still log events."

install -d -m 0750 -o root -g "$ADMIN_USER" "$SECURITY_DATA_DIR" "$SECURITY_DATA_DIR/captures"
touch "$SECURITY_DATA_DIR/events.jsonl"
chown root:"$ADMIN_USER" "$SECURITY_DATA_DIR/events.jsonl"
chmod 0640 "$SECURITY_DATA_DIR/events.jsonl"

cat > /usr/local/sbin/nitro-security-collector <<'PY'
#!/usr/bin/env python3
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

DATA_DIR = Path(os.environ.get("SECURITY_DATA_DIR", "/srv/appdata/security"))
CAPTURE_SECONDS = int(os.environ.get("SECURITY_CAPTURE_SECONDS", "8"))
RETENTION_DAYS = int(os.environ.get("SECURITY_RETENTION_DAYS", "7"))
EVENTS_FILE = DATA_DIR / "events.jsonl"
CAPTURES_DIR = DATA_DIR / "captures"
MAX_EVENTS = 2000
LAST_CAPTURE = 0.0
MIN_CAPTURE_INTERVAL = 20.0


def ensure_dirs():
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_FILE.touch(exist_ok=True)


def trim_events():
    try:
        lines = EVENTS_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        if len(lines) > MAX_EVENTS:
            EVENTS_FILE.write_text("\n".join(lines[-MAX_EVENTS:]) + "\n", encoding="utf-8")
    except OSError:
        pass


def cleanup_old():
    cutoff = time.time() - RETENTION_DAYS * 86400
    for path in CAPTURES_DIR.glob("*"):
        try:
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            pass


def append_event(kind, severity, source, message, capture=None):
    event = {
        "ts": time.time(),
        "kind": kind,
        "severity": severity,
        "source": source,
        "message": message[:1000],
    }
    if capture:
        event["capture"] = capture
    with EVENTS_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    trim_events()


def capture_local_login_failure():
    global LAST_CAPTURE
    now = time.time()
    if now - LAST_CAPTURE < MIN_CAPTURE_INTERVAL:
        return None
    LAST_CAPTURE = now
    cleanup_old()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    video = CAPTURES_DIR / f"tty-failure-{stamp}.mp4"
    audio = CAPTURES_DIR / f"tty-failure-{stamp}.wav"
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return {"status": "skipped", "reason": "ffmpeg not installed"}

    commands = [
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-t", str(CAPTURE_SECONDS), "-f", "v4l2", "-i", "/dev/video0", "-f", "alsa", "-i", "default", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", str(video)],
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-t", str(CAPTURE_SECONDS), "-f", "v4l2", "-i", "/dev/video0", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(video)],
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-t", str(CAPTURE_SECONDS), "-f", "alsa", "-i", "default", str(audio)],
    ]
    last_error = "capture failed"
    for command in commands:
        try:
            result = subprocess.run(command, timeout=CAPTURE_SECONDS + 8, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            target = Path(command[-1])
            if result.returncode == 0 and target.exists() and target.stat().st_size > 0:
                return {"status": "saved", "file": target.name, "seconds": CAPTURE_SECONDS}
            last_error = result.stderr.decode("utf-8", errors="replace")[-300:]
        except Exception as exc:
            last_error = str(exc)
    return {"status": "failed", "reason": last_error}


def classify(entry):
    msg = entry.get("MESSAGE", "")
    unit = entry.get("_SYSTEMD_UNIT", "")
    ident = entry.get("SYSLOG_IDENTIFIER", "")
    comm = entry.get("_COMM", "")
    source = ident or comm or unit
    lower = msg.lower()

    is_tty_login = comm == "login" or ident == "login" or unit.startswith("getty@")
    if is_tty_login and ("authentication failure" in lower or "failed login" in lower or "login incorrect" in lower):
        return "tty_login_failure", "high", source, msg, True
    if ident in {"sshd", "sshd-session"} and ("failed password" in lower or "invalid user" in lower or "authentication failure" in lower):
        return "ssh_login_failure", "medium", source, msg, False
    if "cockpit" in source.lower() and ("authentication failure" in lower or "failed" in lower or "login" in lower):
        return "cockpit_auth_event", "medium", source, msg, False
    if "sudo" in source.lower() and ("authentication failure" in lower or "incorrect password" in lower):
        return "sudo_auth_failure", "medium", source, msg, False
    if "authentication failure" in lower or "failed password" in lower or "invalid user" in lower:
        return "auth_failure", "low", source, msg, False
    return None


def follow_journal():
    command = ["journalctl", "-f", "-n", "0", "-o", "json"]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

    def stop(_signum, _frame):
        proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    assert proc.stdout is not None
    for line in proc.stdout:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        classified = classify(entry)
        if not classified:
            continue
        kind, severity, source, message, should_capture = classified
        capture = capture_local_login_failure() if should_capture else None
        append_event(kind, severity, source, message, capture)


if __name__ == "__main__":
    ensure_dirs()
    append_event("security_monitor_started", "low", "nitro-security-collector", "Security monitor started")
    follow_journal()
PY

chmod 0755 /usr/local/sbin/nitro-security-collector

cat > /etc/systemd/system/nitro-security-collector.service <<EOF
[Unit]
Description=Nitro local security event collector
After=systemd-journald.service

[Service]
Type=simple
Environment=SECURITY_DATA_DIR=$SECURITY_DATA_DIR
Environment=SECURITY_CAPTURE_SECONDS=$SECURITY_CAPTURE_SECONDS
Environment=SECURITY_RETENTION_DAYS=$SECURITY_RETENTION_DAYS
ExecStart=/usr/local/sbin/nitro-security-collector
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
enable_now nitro-security-collector.service

log "Security monitor installed. Dashboard data lives in $SECURITY_DATA_DIR"
