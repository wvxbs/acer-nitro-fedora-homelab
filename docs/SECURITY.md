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


## Local Security Panel

The security stack adds a LAN-only dashboard:

```text
https://security.nitro.lan
```

It shows recent authentication-related events from the host journal, including:

- failed local TTY logins
- failed SSH login attempts
- Cockpit authentication events
- sudo authentication failures
- generic PAM/authentication failures

For privacy and storage safety, webcam/audio capture is intentionally narrow:

- capture is triggered only for failed physical console login events from `login`/TTY/getty
- Cockpit, SSH, sudo and container events are logged but do not trigger camera or microphone
- captures are stored under `/srv/appdata/security/captures` by default
- event metadata is stored in `/srv/appdata/security/events.jsonl`
- default capture length is 8 seconds
- default retention is 7 days

Configure these values in `config/homelab.env`:

```bash
SECURITY_DATA_DIR=/srv/appdata/security
SECURITY_CAPTURE_SECONDS=8
SECURITY_RETENTION_DAYS=7
```

The host service is:

```bash
sudo systemctl status nitro-security-collector.service
sudo journalctl -u nitro-security-collector.service -n 100
```

The dashboard container only receives read-only access to the security data directory. Camera and microphone access stay on the host-side collector.
