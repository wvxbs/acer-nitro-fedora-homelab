# Remote AI Delegation

This homelab has two different AI roles:

- Run agents on the Nitro so the personal Windows machine can stay light.
- Serve small local models from the Nitro for chat, experiments, summaries, and low-stakes coding help.

They are related, but not the same thing.

## Recommended Layout

```text
Windows / phone / another PC
  |
  | Codex App SSH remote project
  v
Nitro Linux user account
  - own ~/.codex
  - own projects
  - own shell permissions
  - can use Docker services

Nitro Docker services
  - Ollama: local model runtime
  - Open WebUI: browser UI for users
  - Caddy: local reverse proxy
```

Use separate Linux users for separate people. Do not share one Codex session, one
`~/.codex`, or one home directory between family members.

Good user model:

```text
wvxbs      admin/developer account
familia    limited operations account
pai        optional separate parent account
mae        optional separate parent account
```

Each Codex user should authenticate Codex in that user's own shell. That keeps
accounts, tokens, project state, and threads separated.

## What LM Studio Is Useful For

LM Studio is useful as:

- a desktop model manager on Windows;
- a local OpenAI-compatible API server;
- a headless runtime on Linux with the `lms` CLI and `llmster` daemon;
- a quick way to test local models against tools that support OpenAI-compatible APIs.

For this server, prefer Docker-managed Ollama/Open WebUI as the default always-on
service. LM Studio is excellent interactively, but it is not the cleanest Docker
primitive for this homelab. If you want LM Studio specifically on the Nitro, run
it as a per-user Linux daemon instead of pretending it is a shared container.

## Local Model Expectations

The Acer Nitro GTX 1650 has 4 GB VRAM. It is useful, but modest.

Good fits:

- `llama3.2:1b`
- `llama3.2:3b`
- `qwen2.5-coder:1.5b`
- `qwen2.5:3b`
- `phi3:mini`

Avoid expecting good performance from large models, huge context windows, or
multiple simultaneous heavy users.

## Start The Docker AI Stack

On the Nitro:

```bash
cd /opt/homelab
docker compose --profile ai up -d
docker exec -it ollama ollama pull llama3.2:3b
docker exec -it ollama ollama pull qwen2.5-coder:1.5b
```

Local URLs through the reverse proxy:

```text
http://openwebui.nitro.lan
http://ollama.nitro.lan
```

Direct service ports:

```text
http://192.168.15.8:3000   Open WebUI
http://192.168.15.8:11434  Ollama API
```

Open WebUI has its own login system. Create one account per person there.

## Codex Remote Delegation

The supported Codex pattern for this homelab is SSH remote projects:

1. Create a separate Linux user for each person that will use Codex.
2. Add that SSH host to the Windows user's `~/.ssh/config`.
3. Install Codex CLI on the Nitro for that Linux user.
4. Authenticate Codex as that Linux user.
5. In the Codex App, open `Settings > Connections`, add the SSH host, and choose
   the remote project folder.

Example Windows SSH config:

```sshconfig
Host nitro-codex-wvxbs
  HostName 192.168.15.8
  User wvxbs
  IdentityFile ~/.ssh/id_ed25519

Host nitro-codex-familia
  HostName 192.168.15.8
  User familia
  IdentityFile ~/.ssh/id_ed25519_familia
```

Confirm SSH before using it in Codex:

```powershell
ssh nitro-codex-wvxbs
```

Install Codex CLI on the Nitro user account:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
codex --version
```

Authenticate on the Nitro:

```bash
codex login --device-auth
```

Device auth is the cleanest path for a headless server. Each person should run
that command in their own Linux user account and sign in with their own ChatGPT
account.

## Codex Automation

For scripted jobs, use `codex exec` in the user's shell:

```bash
codex exec --sandbox workspace-write "summarize this repo and list risky areas"
```

Use this for scheduled or one-shot tasks. Do not expose `codex exec` behind a
public unauthenticated web endpoint.

## Using Nitro Models From Windows Tools

Tools that accept an OpenAI-compatible endpoint can point to the Nitro model
runtime.

Ollama direct API:

```text
http://192.168.15.8:11434
```

If a tool expects an OpenAI-style base URL, try:

```text
http://192.168.15.8:11434/v1
```

For LM Studio on Windows, use it primarily to:

- test models locally on Windows;
- call a remote OpenAI-compatible endpoint when the app/tool supports custom
  providers;
- compare output quality before deciding what model to pull on the Nitro.

Do not leave the Windows LM Studio process as the required backend for the
homelab. The whole point is that the Nitro should be the always-on runtime.

## Security Notes

- Keep Codex authentication per Linux user.
- Never commit `~/.codex/auth.json`, API keys, model tokens, or browser session
  exports.
- Prefer SSH keys over passwords.
- Keep Open WebUI authenticated.
- Do not expose Ollama, Open WebUI, or Codex automation directly to the public
  internet.
- For remote access outside the LAN, use Tailscale instead of port forwarding.
