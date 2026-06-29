#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

WIRED_CONN="${WIRED_CONN:-Wired connection 1}"
WIFI_CONN="${WIFI_CONN:-DVG-5G}"
WIRED_IF="${WIRED_IF:-enp7s0}"
WIFI_IF="${WIFI_IF:-wlp8s0}"
SERVICE_IP="${SERVICE_IP:-192.168.15.8}"
SERVICE_PREFIX="${SERVICE_PREFIX:-24}"
LAN_GATEWAY="${LAN_GATEWAY:-192.168.15.1}"
WIRED_METRIC="${WIRED_METRIC:-100}"
WIFI_METRIC="${WIFI_METRIC:-600}"
HOST_DNS="${HOST_DNS:-$SERVICE_IP $LAN_GATEWAY 1.1.1.1 9.9.9.9}"

require_connection() {
  local name="$1"
  nmcli -t -f NAME connection show | grep -Fxq "$name" || die "NetworkManager connection not found: $name"
}

log "Configuring Ethernet primary route with Wi-Fi fallback"
command -v nmcli >/dev/null 2>&1 || die "nmcli is required"
require_connection "$WIRED_CONN"
require_connection "$WIFI_CONN"

backup_dir="/root/homelab-network-backups/$(date +%Y%m%d-%H%M%S)"
install -d -m 0700 "$backup_dir"
cp -a /etc/NetworkManager/system-connections "$backup_dir/"
nmcli connection show "$WIRED_CONN" > "$backup_dir/wired.before.txt"
nmcli connection show "$WIFI_CONN" > "$backup_dir/wifi.before.txt"
ip -brief address > "$backup_dir/ip-address.before.txt"
ip route show table all > "$backup_dir/routes.before.txt"
log "Backed up NetworkManager profiles to $backup_dir"

log "Pinning service IP $SERVICE_IP/$SERVICE_PREFIX to $WIRED_CONN on $WIRED_IF"
nmcli connection modify "$WIRED_CONN" \
  connection.interface-name "$WIRED_IF" \
  connection.autoconnect yes \
  connection.autoconnect-priority 100 \
  ipv4.method manual \
  ipv4.addresses "$SERVICE_IP/$SERVICE_PREFIX" \
  ipv4.gateway "$LAN_GATEWAY" \
  ipv4.dns "$HOST_DNS" \
  ipv4.route-metric "$WIRED_METRIC" \
  ipv4.never-default no \
  ipv6.method auto \
  ipv6.route-metric "$WIRED_METRIC" \
  ipv6.never-default no

log "Allowing $WIFI_CONN on $WIFI_IF to install a high-metric fallback route"
nmcli connection modify "$WIFI_CONN" \
  connection.interface-name "$WIFI_IF" \
  connection.autoconnect yes \
  connection.autoconnect-priority -50 \
  ipv4.method auto \
  ipv4.route-metric "$WIFI_METRIC" \
  ipv4.never-default no \
  ipv6.method auto \
  ipv6.route-metric "$WIFI_METRIC" \
  ipv6.never-default no

log "Applying NetworkManager changes"
nmcli connection reload
nmcli connection up "$WIRED_CONN"
nmcli connection up "$WIFI_CONN" || warn "Wi-Fi connection did not come up; Ethernet remains configured"

log "Final addresses and routes"
ip -brief address show "$WIRED_IF" || true
ip -brief address show "$WIFI_IF" || true
ip route show default || true
ip -6 route show default || true

log "Connectivity checks"
ping -c 3 -I "$WIRED_IF" "$LAN_GATEWAY"
ping -c 3 -I "$SERVICE_IP" 1.1.1.1

if ip route show default dev "$WIFI_IF" | grep -q '^default '; then
  log "Wi-Fi fallback route is installed with metric $WIFI_METRIC"
else
  warn "Wi-Fi did not receive an IPv4 default route. Check router DHCP if fallback is required."
fi

if command -v docker >/dev/null 2>&1; then
  log "Container network bindings that mention the service IP"
  docker ps --format '{{.Names}} {{.Ports}} {{.Networks}}' | grep -E "$SERVICE_IP|host|0\.0\.0\.0|::" || true
fi

log "Done. Ethernet is primary; Wi-Fi is fallback."
