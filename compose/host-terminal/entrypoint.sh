#!/usr/bin/env bash
set -euo pipefail

username="${TERMINAL_USERNAME:-admin}"
password="${TERMINAL_PASSWORD:-}"
auth_mode="${TERMINAL_AUTH_MODE:-system}"
port="${TERMINAL_INTERNAL_PORT:-7681}"
command=(/usr/local/bin/host-login)
credential_args=()

case "$auth_mode" in
  proxy)
    command=(/usr/local/bin/host-shell)
    ;;
  system)
    command=(/usr/local/bin/host-login)
    ;;
  basic)
    if [[ -z "$password" ]]; then
      printf '%s\n' "TERMINAL_PASSWORD is required when TERMINAL_AUTH_MODE=basic." >&2
      exit 64
    fi

    case "$password" in
      changeme|terminal|password|admin)
        printf '%s\n' "Refusing weak TERMINAL_PASSWORD. Choose a unique password." >&2
        exit 64
        ;;
    esac

    credential_args=(--credential "${username}:${password}")
    command=(/usr/local/bin/host-shell)
    ;;
  *)
    printf 'Unsupported TERMINAL_AUTH_MODE: %s\n' "$auth_mode" >&2
    printf '%s\n' "Use 'proxy' for Caddy auth, 'basic' for ttyd basic auth, or 'system' for the experimental Fedora login prompt." >&2
    exit 64
    ;;
esac

exec ttyd \
  --writable \
  --check-origin \
  --debug 4 \
  --interface 0.0.0.0 \
  --port "$port" \
  "${credential_args[@]}" \
  --terminal-type xterm-256color \
  --client-option "titleFixed=Nitro Terminal" \
  --client-option "fontSize=15" \
  --client-option "fontFamily=ui-monospace, SFMono-Regular, Menlo, Consolas, Liberation Mono, monospace" \
  --client-option "cursorBlink=true" \
  --client-option "scrollback=10000" \
  --client-option 'theme={"background":"#101216","foreground":"#f4f7fb","cursor":"#72bfff","selectionBackground":"#2b3340","black":"#101216","red":"#ff6f76","green":"#45d483","yellow":"#f6c65b","blue":"#72bfff","magenta":"#d6a3ff","cyan":"#68d8d6","white":"#f4f7fb","brightBlack":"#5b6877","brightRed":"#ff9a9f","brightGreen":"#7ee2a4","brightYellow":"#ffe08a","brightBlue":"#a8d8ff","brightMagenta":"#e6c4ff","brightCyan":"#9be7e5","brightWhite":"#ffffff"}' \
  "${command[@]}"
