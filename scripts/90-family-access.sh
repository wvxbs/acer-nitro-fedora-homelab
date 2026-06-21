#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Configuring limited family access"

if ! id -u "$FAMILY_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$FAMILY_USER"
  warn "Created $FAMILY_USER without a password. Set one with: sudo passwd $FAMILY_USER"
else
  log "User $FAMILY_USER already exists."
fi

install -d -m 0755 /etc/polkit-1/rules.d
cat > /etc/polkit-1/rules.d/49-homelab-family-power.rules <<EOF
polkit.addRule(function(action, subject) {
  if (subject.user == "$FAMILY_USER" && (
      action.id == "org.freedesktop.login1.reboot" ||
      action.id == "org.freedesktop.login1.reboot-multiple-sessions" ||
      action.id == "org.freedesktop.login1.power-off" ||
      action.id == "org.freedesktop.login1.power-off-multiple-sessions")) {
    return polkit.Result.YES;
  }
});
EOF

chmod 0644 /etc/polkit-1/rules.d/49-homelab-family-power.rules

log "$FAMILY_USER can use Cockpit and can reboot/power off without broad sudo."
warn "AdGuard Home does not have read-only roles. Create a separate AdGuard login manually if needed."
