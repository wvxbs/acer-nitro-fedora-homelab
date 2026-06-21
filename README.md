# Acer Nitro Fedora Homelab

Bootstrap para reaproveitar um Acer Nitro 5 com i5-9300H, GTX 1650 e SSD de 256 GB como servidor Fedora Server.

O objetivo e rodar tudo com o minimo de friccao:

- Fedora Server com SSH, tampa fechada sem suspender e firewall basico.
- Docker Engine + Compose.
- Driver NVIDIA + NVIDIA Container Toolkit para Plex transcoding, upscaling e workloads CUDA.
- Jellyfin e Plex em containers com suporte a GPU.
- Rclone mount read-only via container: OneDrive aparece como pasta local sob demanda, com cache limitado para nao lotar o SSD.
- Acesso sem abrir portas usando Tailscale.
- Perfil opcional de IA local com Ollama e Open WebUI.
- Perfil opcional de DNS com AdGuard Home para bloqueio conservador de ads/trackers.
- Painel local em `https://nitro.lan` com links e healthchecks dos servicos.
- Monitoramento web com Glances e painel simples da GTX 1650 via `nvidia-smi`.

## Uso Rapido

No Fedora Server recem-instalado:

```bash
sudo dnf install -y git
git clone https://github.com/SEU_USUARIO/acer-nitro-fedora-homelab.git
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

Painel local e proxy reverso:

```bash
cd /opt/homelab
docker compose --profile proxy up -d
```

Abra `https://nitro.lan` para ver links e healthchecks.

Para monitoramento rapido:

```bash
cd /opt/homelab
docker compose --profile ops up -d glances nvidia-web
```

Use `https://glances.nitro.lan` para CPU/RAM/disco/Docker e
`https://gpu.nitro.lan` para a GTX 1650.

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

Isso faz a biblioteca aparecer como pasta local para Jellyfin/Plex, mas os filmes so sao baixados quando lidos. O mount e read-only e o cache VFS tem limite para nao lotar o SSD.

Imagem custom: `wvxbs/rclone-jellyfin`. Veja `docs/RCLONE_JELLYFIN_IMAGE.md`.

## GPU

A GTX 1650 deve aparecer em containers com:

```bash
docker run --rm --gpus all nvidia/cuda:12.5.1-base-ubuntu22.04 nvidia-smi
```

O Plex recebe `NVIDIA_VISIBLE_DEVICES=all`. Para transcoding por hardware, ainda e preciso:

- Plex Pass ativo.
- Habilitar hardware transcoding nas configuracoes do Plex.
- Evitar fechar o notebook de um jeito que abafe a saida de ar.

## IA Local

A GTX 1650 normalmente tem 4 GB de VRAM. Ela aguenta modelos pequenos/quantizados, mas nao espere milagres:

- Bons candidatos: Llama 3.2 1B/3B, Phi-3 mini quantizado, Qwen2.5 3B quantizado.
- Use Ollama/Open WebUI para uma experiencia simples.
- Para workloads pesados, o limite sera VRAM, temperatura e energia.

Depois de subir o perfil `ai`:

```bash
docker exec -it ollama ollama pull llama3.2:3b
```

Open WebUI fica em `https://openwebui.nitro.lan` ou `http://HOST:3000`.

Para delegar Codex e outros fluxos de IA para o Nitro, leia `docs/REMOTE_AI_DELEGATION.md`.

## Estado Atual Replicavel

Leia `docs/CURRENT_STATE.md` para ver o estado esperado do homelab, os servicos,
as URLs, o desenho de rede e a checklist para recriar tudo.

## Arquivos Locais Que Nao Devem Ir Para o Git

- `config/homelab.env`
- `rclone/rclone.conf`
- qualquer chave SSH ou token
- dumps, logs e diretorios `runtime/`

## Publicar no GitHub

Com `gh` autenticado:

```bash
git init
git add .
git commit -m "Initial Fedora homelab bootstrap"
gh repo create acer-nitro-fedora-homelab --public --source=. --remote=origin --push
```
