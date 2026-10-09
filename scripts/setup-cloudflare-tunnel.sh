#!/bin/bash
set -euo pipefail

TUNNEL_NAME="${1:-lex-agent-tunnel}"
PORT="${2:-8080}"

echo "=== Konfiguracja Cloudflare Zero Trust Tunnel dla Lex Agent RPA ==="

if ! command -v cloudflared &> /dev/null; then
    echo "[!] Narzędzie cloudflared nie zostało wykryte."
    echo "[*] Instalacja cloudflared..."
    curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared.deb
    rm cloudflared.deb
fi

echo "[*] Logowanie do Cloudflare..."
cloudflared tunnel login

echo "[*] Tworzenie tunelu: ${TUNNEL_NAME}..."
cloudflared tunnel create "${TUNNEL_NAME}" || true

echo "[*] Konfiguracja routingu na port lokalny localhost:${PORT}..."
cat <<EOF > ~/.cloudflared/config.yml
tunnel: ${TUNNEL_NAME}
credentials-file: ~/.cloudflared/${TUNNEL_NAME}.json

ingress:
  - hostname: lex-agent.internal.domain
    service: http://localhost:${PORT}
  - service: http_status:404
EOF

echo "[+] Tunel Cloudflare Zero Trust został skonfigurowany pomyślnie."
echo "[*] Uruchomienie tunelu w tle: cloudflared tunnel run ${TUNNEL_NAME}"
