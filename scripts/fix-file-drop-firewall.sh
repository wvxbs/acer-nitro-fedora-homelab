#!/usr/bin/env bash
set -euo pipefail

ZONE="${1:-FedoraServer}"

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Run with sudo: sudo $0 ${ZONE}" >&2
  exit 1
fi

echo "Opening File Drop SMB/WSD/mDNS on firewalld zone: ${ZONE}"
firewall-cmd --zone="${ZONE}" --add-service=samba
firewall-cmd --zone="${ZONE}" --add-service=mdns
firewall-cmd --zone="${ZONE}" --add-port=3702/udp
firewall-cmd --zone="${ZONE}" --add-port=5357/tcp
firewall-cmd --runtime-to-permanent

echo "Active zones:"
firewall-cmd --get-active-zones

echo "File Drop firewall rules applied."
