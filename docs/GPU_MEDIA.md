# GPU and Video Workloads

The Nitro has a GTX 1650 with 4 GB VRAM. Use it where it helps, but keep the setup simple:

- Jellyfin can use GPU acceleration when transcoding is unavoidable.
- Direct play is preferred for movies from OneDrive, because it avoids unnecessary load.
- Ollama and local AI workloads can use CUDA, but models must fit inside modest VRAM.
- `https://performance.nitro.lan` is the quick source of truth for GTX 1650 load, VRAM, temperature, power state and the rest of the server load.

Validate container GPU access with:

```bash
docker run --rm --gpus all nvidia/cuda:12.5.1-base-ubuntu22.04 nvidia-smi
```

For host-level checks:

```bash
nvidia-smi
```

## Idle Power

The Nitro is a hybrid Intel iGPU + NVIDIA dGPU notebook. The preferred idle state is:

```text
Intel iGPU: available for display/light graphics
NVIDIA dGPU: runtime suspended/D3 when not doing Jellyfin transcoding or local AI
```

`scripts/35-power-tuning.sh` sets CPU governors to a conservative baseline and writes:

```text
options nvidia NVreg_DynamicPowerManagement=0x02
```

That NVIDIA option takes effect only after the NVIDIA kernel module is reloaded or the host reboots. Until then, the GTX 1650 may stay in `P0` around 16 W even when utilization is 0%.
