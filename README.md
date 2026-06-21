# Acer Nitro Proxmox Homelab

Bootstrap para reaproveitar um Acer Nitro 5 com i5-9300H, GTX 1650, SSD de 256 GB e HD externo de 512 GB como homelab Proxmox.

O desenho atual e deliberado:

- Proxmox VE no metal.
- GPU NVIDIA no host Proxmox, nao passthrough como plano principal.
- LXC `media` privilegiado com acesso a `/dev/nvidia*` e `/dev/dri`.
- Plex instalado nativo no LXC para reduzir atrito com NVIDIA.
- Rclone pull-only dentro do LXC: OneDrive -> HD externo.
- Tailscale no host para acesso sem abrir portas.
- Docker/Compose opcional para workloads gerais sem GPU.

## Por Que Proxmox

O objetivo mudou de "Fedora Server com Docker" para "homelab Proxmox com GPU funcionando". Em notebook com dGPU NVIDIA/Optimus, passthrough PCI para VM pode funcionar, mas e a parte menos garantivel. O caminho mais robusto e manter o driver no host e expor os device nodes para um LXC de media.

## Uso Rapido

No Proxmox VE recem-instalado:

```bash
apt update
apt install -y git
git clone https://github.com/wvxbs/acer-nitro-fedora-homelab.git
cd acer-nitro-fedora-homelab
cp config/homelab.env.example config/homelab.env
nano config/homelab.env
./scripts/bootstrap.sh
reboot
./scripts/healthcheck.sh
```

Sim, o nome remoto ainda contem `fedora` por historico. A arquitetura atual do repo e Proxmox-first.

## Ordem Recomendada

1. Instale Proxmox VE no SSD interno.
2. Use Ethernet no notebook, se possivel.
3. Desative Secure Boot na BIOS para evitar assinatura de modulo NVIDIA.
4. Rode o bootstrap.
5. Reinicie para carregar driver NVIDIA.
6. Rode `./scripts/healthcheck.sh`.
7. Abra o Plex em `http://IP_DO_CT_MEDIA:32400/web`.
8. Configure `rclone config` dentro do CT `media`.
9. Habilite o timer de pull-only dentro do CT.

## Layout

Por padrao:

- Host Proxmox: virtualizacao, driver NVIDIA, storage bind mounts, Tailscale.
- CT 120 `media`: Plex, rclone, acesso a GPU e midia.
- SSD interno: `/srv/appdata`, configs, bancos, transcode.
- HD externo: `/srv/storage`, midia e rips.

## Comandos Uteis

Verificar GPU no host:

```bash
nvidia-smi
```

Verificar GPU no CT:

```bash
pct exec 120 -- nvidia-smi
```

Entrar no CT:

```bash
pct enter 120
```

Configurar OneDrive dentro do CT:

```bash
pct enter 120
su - plex
rclone config
rclone lsd onedrive:
exit
systemctl enable --now rclone-onedrive-pull.timer
```

## O Que Nao E Garantido

GPU passthrough completa da GTX 1650 para uma VM nao e o plano A. Em notebook com Optimus isso depende de IOMMU groups, firmware, VBIOS e comportamento especifico da placa. Este repo foca no caminho mais confiavel para Plex/Jellyfin: driver no host + LXC com devices NVIDIA.

## Arquivos Locais Que Nao Devem Ir Para o Git

- `config/homelab.env`
- `rclone/rclone.conf`
- chaves SSH, tokens, claims Plex permanentes
- dumps, logs e diretorios `runtime/`
