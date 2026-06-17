# GPU, Plex and Video Workloads

## Validate NVIDIA

After reboot:

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.5.1-base-ubuntu22.04 nvidia-smi
```

If `nvidia-smi` fails after reboot, check whether Secure Boot is enabled. Fedora can require module signing/MOK enrollment for the proprietary NVIDIA driver when Secure Boot is on. The lowest-friction homelab path is usually disabling Secure Boot in firmware.

## Plex Hardware Transcoding

Requirements:

- Plex Pass.
- Hardware transcoding enabled in Plex settings.
- Container started with the `media` profile.

Start:

```bash
cd /opt/homelab
docker compose --profile media up -d
```

Watch GPU activity:

```bash
watch -n 1 nvidia-smi
```

## Upscaling

The repo does not install a dedicated upscaler by default because the best tool depends on your workflow. Good next additions:

- Video2X in a separate container for batch jobs.
- ffmpeg with NVENC/NVDEC for transcode jobs.
- Tdarr or Unmanic for automated library processing.

The base NVIDIA Docker runtime is installed so those can be added as Compose services later.
