# Acer Nitro Fedora Homelab

Bootstrap para reaproveitar um Acer Nitro 5 com i5-9300H, GTX 1650 e SSD de 256 GB como servidor Fedora Server.

O objetivo e rodar tudo com o minimo de friccao:

- Fedora Server com SSH, tampa fechada sem suspender e firewall basico.
- Docker Engine + Compose.
- Driver NVIDIA + NVIDIA Container Toolkit para Jellyfin, Ollama e workloads CUDA.
- Jellyfin em container com suporte a GPU.
- Rclone mount read-only via container: OneDrive aparece como pasta local sob demanda, com cache limitado para nao lotar o SSD.
- Acesso sem abrir portas usando Tailscale.
- Perfil opcional de IA local com Ollama e Open WebUI.
- OpenClaw opcional no perfil de IA, apontando para Ollama local.
- Delegacao de Codex por SSH remoto, com usuarios Linux separados por pessoa.
- Perfil opcional de DNS com AdGuard Home para bloqueio conservador de ads/trackers.
- File Drop opcional: pasta SMB3 temporaria na LAN para arrastar arquivos entre Windows, macOS e Linux sem login.
- Terminal web opcional em `terminal.nitro.lan` para emergencia quando SSH nao estiver disponivel.
- Painel local em `https://nitro.lan` com links e healthchecks dos servicos.
- Monitoramento web com Glances e painel simples da GTX 1650 via `nvidia-smi`.

## Uso Rapido

No Fedora Server recem-instalado:

```bash
sudo dnf install -y git
git clone https://github.com/wvxbs/acer-nitro-fedora-homelab.git
cd acer-nitro-fedora-homelab
cp config/homelab.env.example config/homelab.env
nano config/homelab.env
sudo ./scripts/bootstrap.sh
```

Se voce ainda nao tiver subido o repo para o GitHub, pode copiar esta pasta por SSH/pendrive e rodar localmente.

## Ordem Recomendada no Dia

1. Instale Fedora Server.
2. Conecte o notebook por cabo Ethernet, se possivel.
3. Rode o bootstrap.
4. Reinicie depois da instalacao NVIDIA.
5. Rode `./scripts/healthcheck.sh`.
6. Configure o rclone com `rclone config`.
7. Configure o rclone e suba o mount sob demanda do OneDrive via Docker:

```bash
cd /opt/homelab
docker compose --profile media up -d rclone-jellyfin jellyfin
```

8. Suba os containers:

```bash
cd /opt/homelab
docker compose --profile media up -d
```

Para DNS com AdGuard Home:

```bash
cd /opt/homelab
docker compose --profile dns up -d
```

Admin UI: `http://HOST:3001`. Leia `docs/DNS.md` antes de apontar o roteador para ele.

File Drop temporario na LAN:

```bash
cd /opt/homelab
docker compose --profile drop up -d --build
```

Abra `\\192.168.15.8\drop` no Windows ou `smb://192.168.15.8/drop` no macOS/Linux. Use visitante/guest, sem usuario e sem senha. Se precisar de fallback autenticado para Windows, defina `FILE_DROP_USERNAME` e `FILE_DROP_PASSWORD` apenas no `.env` local. Leia `docs/FILE_DROP.md`.

Painel local e proxy reverso:

```bash
cd /opt/homelab
docker compose --profile proxy up -d
```

Abra `https://nitro.lan` para ver links e healthchecks.

Para monitoramento rapido:

```bash
cd /opt/homelab
docker compose --profile ops up -d glances performance-web
```

Use `https://performance.nitro.lan` para CPU/GPU/RAM/VRAM/bateria/discos/rede
com graficos, e `https://glances.nitro.lan` como referencia completa estilo btop.
`https://gpu.nitro.lan` continua como alias do painel consolidado.

Terminal web de emergencia:

```bash
cd /opt/homelab
docker compose --profile terminal up -d --build host-terminal
```

Configure `TERMINAL_PASSWORD`/`TERMINAL_PASSWORD_HASH` antes de subir. O Caddy
pede login do browser e abre um shell do host depois da autenticacao. Abra
`http://terminal.nitro.lan` e pare o container quando terminar. Leia
`docs/HOST_TERMINAL.md`.

Para IA local:

```bash
cd /opt/homelab
docker compose --profile ai up -d
```

## Rede Sem Abrir Portas

O caminho de menor dor para sua rede com dois roteadores e sem port-forward e Tailscale. Ele usa conexoes de saida e cria uma rede privada entre seus dispositivos.

- Da rede de casa, voce acessa pelo IP local ou pelo nome `.local`.
- Da rede do escritorio, voce acessa pelo IP Tailscale ou MagicDNS.
- Nao precisa abrir portas no roteador da Vivo nem no roteador Wi-Fi 6E.

Opcionalmente, se o roteador de casa puder operar em modo AP/bridge, isso simplifica tudo na LAN. Mas o setup deste repo nao depende disso.

## Armazenamento

Por padrao tudo fica no SSD interno:

- `/srv/appdata`: configuracoes, bancos, caches dos containers e cache VFS do rclone.
- `/srv/storage/media`: midia local e ponto de montagem do OneDrive.
- `/srv/storage/media/onedrive`: OneDrive montado sob demanda via rclone.

O script nao formata discos automaticamente e nao depende de disco adicional.

## OneDrive Sob Demanda

O rclone roda preferencialmente como container e monta o OneDrive sob demanda:

```bash
docker compose --profile media up -d rclone-jellyfin jellyfin
```

Isso faz a biblioteca aparecer como pasta local para o Jellyfin, mas os filmes so sao baixados quando lidos. O mount e read-only e o cache VFS tem limite para nao lotar o SSD.

Imagem custom: `wvxbs/rclone-jellyfin`. Veja `docs/RCLONE_JELLYFIN_IMAGE.md`.

## GPU

A GTX 1650 deve aparecer em containers com:

```bash
docker run --rm --gpus all nvidia/cuda:12.5.1-base-ubuntu22.04 nvidia-smi
```

Jellyfin, Ollama e os monitores recebem `NVIDIA_VISIBLE_DEVICES=all` quando precisam da GPU. Para video, mantenha preferencialmente direct play; transcoding por hardware deve ser usado so quando necessario.

Evite fechar o notebook de um jeito que abafe a saida de ar.

## IA Local

A GTX 1650 normalmente tem 4 GB de VRAM. Ela aguenta modelos pequenos/quantizados, mas nao espere milagres:

- Bons candidatos: Llama 3.2 1B/3B, Phi-3 mini quantizado, Qwen2.5 3B quantizado.
- Para OpenClaw local, comece com `llama3.2:3b`; tente `gemma4`/`gemma3:4b` so depois de validar desempenho.
- Use Ollama/Open WebUI para uma experiencia simples.
- Para workloads pesados, o limite sera VRAM, temperatura e energia.

Depois de subir o perfil `ai`:

```bash
docker exec -it ollama ollama pull llama3.2:3b
```

OpenClaw local via Ollama:

```bash
cd /opt/homelab
docker compose --profile ai up -d ollama openclaw-gateway
docker compose --profile ai-tools run --rm openclaw-cli \
  onboard --non-interactive \
  --auth-choice ollama \
  --custom-base-url "http://ollama:11434" \
  --custom-model-id "llama3.2:3b" \
  --accept-risk
docker compose --profile ai restart openclaw-gateway
```

Open WebUI fica em `https://openwebui.nitro.lan` ou `http://HOST:3000`.
OpenClaw fica em `https://openclaw.nitro.lan` ou `http://HOST:18789`.

Para delegar Codex e outros fluxos de IA para o Nitro, leia `docs/REMOTE_AI_DELEGATION.md`.

## Estado Atual Replicavel

Leia `docs/CURRENT_STATE.md` para ver o estado esperado do homelab, os servicos,
as URLs, o desenho de rede e a checklist para recriar tudo.

## Arquivos Locais Que Nao Devem Ir Para o Git

- `config/homelab.env`
- `/opt/homelab/.env`
- `rclone/rclone.conf`
- qualquer chave SSH ou token
- hashes de senha reais, mesmo bcrypt
- dumps, logs e diretorios `runtime/`

## Publicar no GitHub

Com `gh` autenticado, para um repo novo:

```bash
git init
git add .
git commit -m "Initial Fedora homelab bootstrap"
gh repo create acer-nitro-fedora-homelab --public --source=. --remote=origin --push
```

Para este repo ja publicado:

```bash
git remote -v
git status --short
git push origin main
```
