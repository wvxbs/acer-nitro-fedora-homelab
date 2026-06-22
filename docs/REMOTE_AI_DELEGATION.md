# Remote AI Delegation

The Nitro has two distinct AI roles:

1. **Local model runtime**: Ollama and Open WebUI run on the Nitro so phones and PCs can use small local models without keeping LM Studio open on a personal machine.
2. **Codex execution host**: Codex work can run against projects on the Nitro through SSH remote projects, with one Linux user and one Codex login per person.

Do not treat these as one shared account. The correct model is isolated users.

## What Is Supported For Codex

The supported homelab pattern is:

```text
Codex App on a personal device
  -> SSH remote project
  -> Nitro Linux user
  -> that user's ~/.codex, projects, shell and permissions
```

This lets the Nitro do the shell/file work while the personal device sends prompts, approvals and follow-ups. It is the practical way to delegate agent work to the server.

Avoid exposing `codex app-server` or `codex exec` as an unauthenticated LAN web service. Codex app-server has local/SSH integration use cases, but a raw listener is not the right family-facing control plane for this homelab.

For scripted jobs, use `codex exec` from that user's shell or a private scheduler. For interactive work, use Codex App remote SSH projects.

## Multi-User Layout

Recommended Linux users:

```text
wvxbs  admin/developer account
mae    mother's Codex account and projects
pai    father's Codex account and projects
```

Each user gets:

```text
/home/<user>/projects
/home/<user>/.codex
/home/<user>/.ssh
```

Each person must sign in to Codex with their own ChatGPT/OpenAI account. Do not copy your `~/.codex/auth.json` to another person's account.

## Prepare Users

Set this in `config/homelab.env` before bootstrap, or export it before running the script:

```bash
CODEX_USERS="wvxbs mae pai"
```

Then run:

```bash
sudo ./scripts/85-codex-users.sh
```

The script creates missing users with password login locked. Add SSH keys before remote use:

```bash
sudo install -d -m 0700 -o mae -g mae /home/mae/.ssh
sudoedit /home/mae/.ssh/authorized_keys
sudo chown mae:mae /home/mae/.ssh/authorized_keys
sudo chmod 0600 /home/mae/.ssh/authorized_keys
```

Repeat for `pai`.

## Configure SSH From A Client

On the computer running Codex App, add aliases to `~/.ssh/config`:

```sshconfig
Host nitro-codex-wvxbs
  HostName 192.168.15.8
  User wvxbs
  IdentityFile ~/.ssh/id_ed25519

Host nitro-codex-mae
  HostName 192.168.15.8
  User mae
  IdentityFile ~/.ssh/id_ed25519_mae

Host nitro-codex-pai
  HostName 192.168.15.8
  User pai
  IdentityFile ~/.ssh/id_ed25519_pai
```

Validate before opening Codex:

```bash
ssh nitro-codex-mae
```

## Install And Authenticate Codex On The Nitro

Run as each Linux user that will use Codex:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
codex --version
codex login --device-auth
```

Device auth is the cleanest path for a server because the browser login happens on another device while credentials are stored under that Linux user's own `~/.codex`.

## Use From Codex App

In Codex App:

1. Open **Settings > Connections**.
2. Add or enable the SSH host alias, for example `nitro-codex-mae`.
3. Choose a project folder under `/home/mae/projects`.
4. Start a thread there.

The prompts and approvals happen from the personal device. Commands and file edits happen on the Nitro under the selected Linux user.

## Codex Automation

For one-shot private jobs:

```bash
cd ~/projects/some-repo
codex exec --sandbox workspace-write "summarize this repo and list risky areas"
```

Use `codex exec` for scheduled or scripted tasks. Keep it private, per-user, and never expose it directly to the internet or to a shared web button.

## Local Models

Start the local model stack:

```bash
cd /opt/homelab
docker compose --profile ai up -d
docker exec -it ollama ollama pull llama3.2:3b
docker exec -it ollama ollama pull qwen2.5-coder:1.5b
```

Local URLs:

```text
https://openwebui.nitro.lan
https://ollama.nitro.lan
```

Direct endpoints:

```text
http://192.168.15.8:3000   Open WebUI
http://192.168.15.8:11434  Ollama API
http://192.168.15.8:11434/v1 OpenAI-compatible Ollama API
```

Configured model aliases:

```text
nitro-coder -> qwen2.5-coder:1.5b
nitro-chat  -> llama3.2:3b
```

Use `nitro-coder` for lightweight coding/help tasks and `nitro-chat` for general chat.

Open WebUI has its own login system. Create one Open WebUI account per person.

## LM Studio And LM Link Role

Use LM Studio on Windows mainly as a model tester, client, or LM Link participant. LM Link can route requests from one machine to a model loaded on another linked machine, while the local app/API still feels local to the caller. In this homelab, that is useful in two directions:

- Dell/Windows can use a model running on the Nitro without keeping the heavy model loaded on the Dell.
- A stronger future machine could serve models while the Nitro continues to host Jellyfin, DNS, dashboards and lightweight agents.

LM Link is not a replacement for Codex remote SSH projects. It routes model inference; it does not isolate Codex accounts, project files, shells, approvals or agent state. For Codex delegation, keep using per-user SSH remote projects.

The always-on default service remains Nitro-hosted Ollama/Open WebUI. If a tool accepts an OpenAI-compatible endpoint, point it to:

```text
http://192.168.15.8:11434/v1
```

Use model name `nitro-coder` for the default remote coding model.

LM Studio also exposes OpenAI-compatible endpoints when its server is running, and its headless `llmster` daemon is a viable future alternative to Ollama if we decide LM Studio should be the server runtime. For now, avoid running both Ollama and LM Studio as competing always-on model servers on the GTX 1650 unless there is a specific test.

The GTX 1650 has 4 GB VRAM. Good model candidates:

```text
llama3.2:1b
llama3.2:3b
qwen2.5-coder:1.5b
qwen2.5:3b
phi3:mini
```

Avoid large models, huge context windows and multiple heavy simultaneous generations.

## Security Notes

- Keep Codex authentication per Linux user.
- Never commit or share `~/.codex/auth.json`.
- Prefer SSH keys over passwords.
- Keep Open WebUI authenticated.
- Do not expose Ollama, Open WebUI or Codex automation directly to the public internet.
- For remote access outside the LAN, use Tailscale instead of port forwarding.
