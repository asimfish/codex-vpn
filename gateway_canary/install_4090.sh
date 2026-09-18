#!/bin/sh
set -eu
root="$HOME/.local/share/unified-ip-watch/gateway-canary"
mkdir -p "$root" "$HOME/.config/systemd/user"
cp gateway.py run.py config.example.json gateway-canary.service "$root"/
if [ ! -e "$root/config.json" ]; then cp "$root/config.example.json" "$root/config.json"; fi
chmod 700 "$root"; chmod 600 "$root/config.json"
cp "$root/gateway-canary.service" "$HOME/.config/systemd/user/gateway-canary.service"
systemctl --user daemon-reload
systemctl --user disable --now gateway-canary.service >/dev/null 2>&1 || true
echo "Installed isolated canary in $root"
echo "Current mode: $(python3 -c 'import json;print(json.load(open(\"'$root'/config.json\"))[\"mode\"])')"
echo "Service remains disabled; edit config.json before enabling."
