#!/usr/bin/env bash
set -euo pipefail

ZONE="${1:-FedoraServer}"
JAVA_PORT="${MINECRAFT_JAVA_PORT:-25565}"
BEDROCK_PORT="${MINECRAFT_BEDROCK_PORT:-19132}"

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Run with sudo: sudo $0 ${ZONE}" >&2
  exit 1
fi

echo "Opening Minecraft Java/Bedrock on firewalld zone: ${ZONE}"
firewall-cmd --zone="${ZONE}" --add-port="${JAVA_PORT}/tcp"
firewall-cmd --zone="${ZONE}" --add-port="${BEDROCK_PORT}/udp"
firewall-cmd --runtime-to-permanent

echo "Active zones:"
firewall-cmd --get-active-zones

echo "Minecraft firewall rules applied."
