
## Install on 4090 from GitHub

```bash
git clone https://github.com/asimfish/codex-vpn.git
cd codex-vpn
git checkout feat/initial-release
sh gateway_canary/install_4090.sh
```

This installs a user-level canary relay at `~/.local/share/unified-ip-watch/gateway-canary`, keeps `config.json` mode 600, and leaves the service disabled. Edit the private `config.json` with your dedicated upstream URL, then start it only for a dedicated Codex test session:

```bash
systemctl --user enable --now gateway-canary.service
curl http://127.0.0.1:47891/health
```

Set `mode` to `observe` first. The relay never changes Clash port 7890, TUN, DNS or existing Codex sessions. `inject` requires repeated fixed-account/fixed-model/fixed-egress canary evidence and expires after `ttl_seconds`.
