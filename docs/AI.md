# Local AI Notes

The GTX 1650 is useful, but modest. Most Nitro 5 GTX 1650 configs have 4 GB VRAM, so the sweet spot is small quantized models.

## Start

Set this in `config/homelab.env` before bootstrap, or run the script later:

```bash
INSTALL_AI=1
```

Start services:

```bash
cd /opt/homelab
docker compose --profile ai up -d
```

Pull a small model:

```bash
docker exec -it ollama ollama pull llama3.2:3b
docker exec -it ollama ollama run llama3.2:3b
```

Other candidates:

```bash
docker exec -it ollama ollama pull phi3:mini
docker exec -it ollama ollama pull qwen2.5:3b
```

Open WebUI:

```text
http://openwebui.nitro.lan
http://HOST:3000
```

The base dashboard also links to it:

```text
http://nitro.lan
```

## Expectations

- Good: chat with small models, embeddings, light coding help, summaries.
- Possible but limited: upscaling/transcoding adjacent workflows and small vision models.
- Not ideal: large LLMs, high concurrency, giant context windows.

If a model does not fit in VRAM, Ollama may spill to CPU and get slow.

## Codex Delegation

Do not run one shared Codex container for the whole family. Use separate Linux
users on the Nitro and connect the Codex App to the Nitro over SSH. Each person
gets their own home directory, projects, `~/.codex`, login tokens, and threads.

See:

```text
docs/REMOTE_AI_DELEGATION.md
```
