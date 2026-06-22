# Security Notes

Defaults are practical, not paranoid:

- SSH enabled.
- Root SSH login disabled.
- Password SSH login left enabled at first so you do not lock yourself out.
- Firewall allows SSH and mDNS.
- No router port-forwarding is required.
- Tailscale is the preferred remote/private access layer.

After confirming your SSH key works, consider:

```bash
sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config.d/99-homelab.conf
sudo sshd -t
sudo systemctl reload sshd
```

Never commit:

- `config/homelab.env`
- `rclone/rclone.conf`
- Tailscale auth keys
- SSH private keys
