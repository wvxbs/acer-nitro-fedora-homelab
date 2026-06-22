# Static Sites

The homelab can host small static websites from the Fedora server without exposing the whole machine directly to the internet.

## RCF Eventos

Local staging URL:

```text
https://rcfeventos.nitro.lan
```

Put the website files here on the deployed server:

```text
/opt/homelab/sites/rcfeventos/
```

The directory should contain the same static files normally uploaded by FileZilla, usually `index.html`, CSS, JavaScript, images and downloadable files. Do not commit client FTP credentials, private files, or production secrets to this repository.

## Safe Exposure Options

Preferred order:

1. **LAN only**: keep `rcfeventos.nitro.lan` private for testing and family use.
2. **Cloudflare Tunnel**: expose only the site hostname to the public internet without router port-forwarding. This is the safest public option for this homelab.
3. **Router port-forwarding**: avoid unless there is a specific reason. If used, forward only 80/443 to Caddy and keep Fedora/Cockpit/Portainer/SSH unreachable from the internet.

For the current `www.rcfeventos.com.br` domain, the clean migration path is to keep Locaweb as-is until the local copy is tested, then point only the public hostname to a tunnel or reverse proxy target.

## Deploy Notes

Caddy serves this as a plain static site. PHP, WordPress, databases and mail forms need separate handling; do not copy old server-side scripts blindly.
