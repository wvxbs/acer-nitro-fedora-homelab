# Security Notes

Defaults are practical, not paranoid:

- SSH enabled.
- Root SSH login disabled.
- Password SSH login left enabled at first so you do not lock yourself out.
- Firewall allows SSH and mDNS.
- No router port-forwarding is required.
- Tailscale is the preferred remote/private access layer.
- File Drop, when enabled, is guest SMB3 for trusted LAN use only. Optional
  fallback SMB credentials must stay in the local `.env`.
- Host Terminal, when enabled, is a browser-accessible host terminal protected
  by Caddy basic auth and a loopback-only Docker bind. Start it only when
  needed, stop it after use, and never expose it with router port-forwarding. It
  runs as a privileged container to enter host namespaces on Fedora; access is
  root-equivalent after the Caddy password succeeds. Avoid direct ttyd `basic`
  mode because ttyd logs basic-auth credentials in base64 at startup.
- The latest local security dashboard helper is preserved at
  `compose/security/server.py`; it stores events/captures under
  `SECURITY_DATA_DIR`, defaulting to `/srv/appdata/security`.

After confirming your SSH key works, consider:

```bash
sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config.d/99-homelab.conf
sudo sshd -t
sudo systemctl reload sshd
```

Never commit:

- `config/homelab.env`
- `/opt/homelab/.env`
- `rclone/rclone.conf`
- Tailscale auth keys
- SSH private keys
- service passwords, API tokens, and real bcrypt password hashes
