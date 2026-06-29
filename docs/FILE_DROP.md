# File Drop

O File Drop e uma pasta temporaria de rede para transferencias rapidas dentro da LAN. Ele usa SMB2/SMB3, aceita acesso como visitante sem usuario/senha quando o cliente permite, e limpeza automatica.

Ele nao usa SMB1/CIFS legado. No Windows, nao habilite o recurso antigo "SMB 1.0/CIFS File Sharing Support".

Windows 11 recente pode bloquear SMB guest por politica do proprio cliente. Se isso acontecer, defina um usuario e senha locais em `/opt/homelab/.env` ou `config/homelab.env`; o servidor tratara essa autenticacao como SMB real e gravara tudo no mesmo drop, sem mexer em politica local do Windows.

## Start

```bash
cd /opt/homelab
docker compose --profile drop up -d --build
```

Por padrao:

```text
Host: 192.168.15.8
Share: drop
Path no servidor: /srv/storage/drop
TTL: 24 horas
Limite alvo: 100G
Acesso primario: visitante/guest, sem usuario e sem senha
Fallback Windows: opcional, definido por FILE_DROP_USERNAME/FILE_DROP_PASSWORD
```

## Acesso

Windows Explorer:

```text
\\192.168.15.8\drop
```

Entre como visitante/guest se o Windows oferecer essa opcao. Se aparecer a mensagem de politica bloqueando convidado nao autenticado, defina `FILE_DROP_USERNAME` e `FILE_DROP_PASSWORD` localmente, suba o stack de novo e use essas credenciais. Nao habilite SMB1.

macOS Finder:

```text
smb://192.168.15.8/drop
```

Linux Files/Nautilus/Dolphin:

```text
smb://192.168.15.8/drop
```

Use o modo Anonimo/Convidado quando o gerenciador perguntar.

Se a descoberta da rede estiver funcionando, o container anuncia `nitro-drop` por WSD para o Windows e o host anuncia o servico SMB por Bonjour/Avahi para macOS e Linux. Ainda assim, o caminho direto por IP e o modo mais previsivel e nao exige habilitar nenhum recurso legado.

## Se nao conectar de outro dispositivo

Se o dashboard marcar o File Drop como online, mas Windows Explorer, iPhone Files
ou Finder nao conseguirem abrir, quase sempre e o firewall do Fedora bloqueando
SMB na zona da LAN. O Samba deve estar ouvindo em `0.0.0.0:445`; libere a zona
ativa do host:

```bash
sudo firewall-cmd --zone=FedoraServer --add-service=samba
sudo firewall-cmd --zone=FedoraServer --add-service=mdns
sudo firewall-cmd --zone=FedoraServer --add-port=3702/udp
sudo firewall-cmd --zone=FedoraServer --add-port=5357/tcp
sudo firewall-cmd --runtime-to-permanent
```

Ou use o reparo pronto:

```bash
cd /opt/homelab
sudo ./scripts/fix-file-drop-firewall.sh
```

Depois tente novamente:

```text
Windows: \\192.168.15.8\drop
iPhone/macOS/Linux: smb://192.168.15.8/drop
Login preferido: visitante/guest, sem usuario e sem senha
Fallback Windows: credenciais locais em FILE_DROP_USERNAME/FILE_DROP_PASSWORD
```

Se ainda falhar, confirme que o cliente esta na mesma LAN `192.168.15.0/24` e
que o roteador nao esta com isolamento de clientes Wi-Fi ativado.

## Comportamento

- Qualquer pessoa na LAN que alcance `192.168.15.8` pode ler, escrever e apagar.
- Guest e aceito para clientes que permitem SMB guest.
- `drop` / `drop` e aceito para Windows 11 quando ele bloqueia guest; qualquer conexao aceita e gravada no disco como o usuario interno `filedrop`.
- Arquivos com mais de `FILE_DROP_TTL_HOURS` sao apagados pelo sidecar `file-drop-cleanup`.
- Se a pasta passar de `FILE_DROP_MAX_SIZE`, os itens de topo mais antigos sao apagados ate voltar para baixo do limite.
- O limite nao e quota dura. Durante uma copia grande, o uso pode passar do alvo ate o ciclo de limpeza seguinte.

## Config

Edite `config/homelab.env` antes de rodar o bootstrap:

```bash
FILE_DROP_DIR=/srv/storage/drop
FILE_DROP_SHARE_NAME=drop
FILE_DROP_WORKGROUP=WORKGROUP
FILE_DROP_NETBIOS_NAME=NITRO-DROP
FILE_DROP_HOSTNAME=nitro-drop
FILE_DROP_GUEST_USER=filedrop
FILE_DROP_USERNAME=
FILE_DROP_PASSWORD=
FILE_DROP_TTL_HOURS=24
FILE_DROP_MAX_SIZE=100G
FILE_DROP_CLEANUP_INTERVAL_SECONDS=300
```

Deixe `FILE_DROP_USERNAME` e `FILE_DROP_PASSWORD` vazios para guest-only. Se
precisar atravessar a politica de guest do Windows, preencha ambos com valores
unicos no arquivo local nao versionado. O container recusa senhas triviais como
`drop`, `password`, `changeme`, `admin` e `guest`.

Depois reaplique o bundle:

```bash
sudo ./scripts/70-services.sh
cd /opt/homelab
docker compose --profile drop up -d --build
```

## Security

Este servico prioriza friccao baixa. Guest continua aberto para clientes que aceitam guest; o login autenticado e opcional e deve ficar somente no `.env` local. Use apenas em rede domestica confiavel ou atras do Tailscale/VPN, e nunca exponha SMB para a internet.
