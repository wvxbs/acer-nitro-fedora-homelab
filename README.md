# Acer Nitro Fedora Homelab

Bootstrap para reaproveitar um Acer Nitro 5 com i5-9300H, GTX 1650, SSD de 256 GB e HD externo de 512 GB como servidor Fedora Server.

O objetivo e rodar tudo com o minimo de friccao:

- Fedora Server com SSH, tampa fechada sem suspender e firewall basico.
- Docker Engine + Compose.
- Driver NVIDIA + NVIDIA Container Toolkit para Plex transcoding, upscaling e workloads CUDA.
- Plex em container com suporte a GPU.
- Rclone em modo pull-only: OneDrive -> HD externo, sem sincronizar mudancas locais de volta.
- Acesso sem abrir portas usando Tailscale.
- Perfil opcional de IA local com Ollama e Open WebUI.

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
7. Habilite o timer de download do OneDrive:

```bash
sudo systemctl enable --now rclone-onedrive-pull.timer
```

8. Suba os containers:

```bash
cd /opt/homelab
docker compose --profile media up -d
```

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

Por padrao:

- SSD interno: `/srv/appdata`, `/srv/docker`, caches e bancos dos containers.
- HD externo 5400 rpm: `/srv/storage`, midia e rips.
- Midia final: `/srv/storage/media`.
- Downloads/pull do OneDrive: `/srv/storage/incoming/onedrive`.

O script nao formata discos automaticamente. Ele so cria ponto de montagem via UUID se voce preencher `EXTERNAL_DISK_UUID`.

## OneDrive Pull-Only

O rclone roda como timer systemd e executa:

```bash
rclone sync "$ONEDRIVE_REMOTE:$ONEDRIVE_PATH" "$ONEDRIVE_LOCAL_PATH"
```

Isso faz a maquina refletir a pasta do OneDrive. Mudancas locais nao sao enviadas para o OneDrive. Se voce apagar localmente, o proximo pull baixa de novo, desde que o arquivo ainda exista no OneDrive.

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

Open WebUI fica em `http://HOST:3000`.

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

