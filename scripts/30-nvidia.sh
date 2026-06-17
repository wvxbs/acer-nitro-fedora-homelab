#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
require_root
load_config

log "Installing NVIDIA driver and container toolkit"

dnf_install fedora-workstation-repositories || true
dnf install -y \
  "https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm" \
  "https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm"

dnf upgrade -y --refresh
dnf_install akmod-nvidia xorg-x11-drv-nvidia-cuda xorg-x11-drv-nvidia-power nvidia-vaapi-driver libva-utils

curl -fsSL https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo \
  -o /etc/yum.repos.d/nvidia-container-toolkit.repo
dnf_install nvidia-container-toolkit

nvidia-ctk runtime configure --runtime=docker || true
systemctl restart docker || true

log "NVIDIA packages installed. Reboot is usually required for akmods to build and load."

