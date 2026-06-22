# GPU and Video Workloads

The Nitro has a GTX 1650 with 4 GB VRAM. Use it where it helps, but keep the setup simple:

- Jellyfin can use GPU acceleration when transcoding is unavoidable.
- Direct play is preferred for movies from OneDrive, because it avoids unnecessary load.
- Ollama and local AI workloads can use CUDA, but models must fit inside modest VRAM.
- `https://gpu.nitro.lan` is the quick source of truth for GTX 1650 load, VRAM, temperature and power state.

Validate container GPU access with:

```bash
docker run --rm --gpus all nvidia/cuda:12.5.1-base-ubuntu22.04 nvidia-smi
```

For host-level checks:

```bash
nvidia-smi
```
