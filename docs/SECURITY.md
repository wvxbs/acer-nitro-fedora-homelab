# Security Notes

Defaults are practical, not paranoid:

- SSH enabled on the Proxmox host.
- Root SSH login set to `prohibit-password`.
- Password SSH login left enabled at first so you do not lock yourself out.
- Proxmox web UI should stay on LAN/Tailscale only.
- No router port-forwarding is required.
- Tailscale is the preferred remote/private access layer.

After confirming your SSH key works, consider disabling password SSH login:

```bash
sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config.d/99-homelab.conf
sshd -t
systemctl reload ssh
```

Do not expose these to the public internet:

- Proxmox web UI, port `8006`.
- SSH, unless protected by Tailscale or another private VPN.
- Plex, unless you intentionally configure Plex remote access.

Never commit:

- `config/homelab.env`
- `rclone/rclone.conf`
- Tailscale auth keys
- SSH private keys
- Plex claim tokens
