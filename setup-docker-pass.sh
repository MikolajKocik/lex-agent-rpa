#!/bin/bash
set -e

echo "==> Instalowanie pass, gnupg oraz golang-docker-credential-helpers..."
sudo apt update
sudo apt install -y pass gnupg golang-docker-credential-helpers

# change template for your data
KEY_DETAILS_FILE=$(mktemp)
cat <<EOF > "$KEY_DETAILS_FILE"
Key-Type: RSA
Key-Length: 4096
Key-Usage: sign,encrypt
Name-Real: mkocik
Name-Email: mikolajkocik@onet.pl
Expire-Date: 3m
Passphrase: SuperTajneHaslo321
%commit
EOF

echo "==> Generowanie klucza GPG..."
gpg --batch --generate-key "$KEY_DETAILS_FILE"
rm -f "$KEY_DETAILS_FILE"

# download generated key id
KEY_ID=$(gpg --list-secret-keys --keyid-format LONG "mikolajkocik@onet.pl" | grep -E '^sec' | awk '{print $2}' | cut -d'/' -f2)

if [ -z "$KEY_ID" ]; then
    echo "Błąd: Nie udało się odnaleźć ID klucza GPG."
    exit 1
fi

echo "==> Znaleziono ID klucza GPG: $KEY_ID"

# initialize pass storage
echo "==> Inicjalizacja pass za pomocą klucza $KEY_ID..."
pass init "$KEY_ID"

# configure file:  ~/.docker/config.json
mkdir -p ~/.docker
CONFIG_FILE="$HOME/.docker/config.json"

if [ -f "$CONFIG_FILE" ]; then
    # if file exists, we add "credsStore": "pass"
    python3 -c "
        import json, os
        path = os.path.expanduser('~/.docker/config.json')
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except Exception:
            data = {}
        data['credsStore'] = 'pass'
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
    "
else
    # create new one if file not exists
    cat <<EOF > "$CONFIG_FILE"
{
    "credsStore": "pass"
}
EOF
fi

echo "==> Configuration completed successfully!"