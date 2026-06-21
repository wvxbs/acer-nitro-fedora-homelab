# Local AI

The GTX 1650 usually has 4 GB VRAM. Treat local AI as a small-model playground, not a serious inference server.

Recommended starting point on Proxmox:

- Keep Plex/GPU media as the priority.
- Run AI in a separate CT or VM only after media is stable.
- Prefer CPU or very small quantized models unless you confirm GPU memory headroom.

Good candidates:

- Llama 3.2 1B/3B quantized.
- Phi-3 mini quantized.
- Qwen small models quantized.

Avoid putting heavy AI and Plex transcoding on the GPU at the same time. The card is useful, but VRAM and thermals are the hard limits.
