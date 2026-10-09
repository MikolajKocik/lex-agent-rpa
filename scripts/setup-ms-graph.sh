#!/bin/bash
set -e

APP_NAME="${1:-lex-agent-rpa-graph}"
GRAPH_API_ID="00000003-0000-0000-c000-000000000000"
MAIL_READ_ROLE_ID="81079e63-4b69-4568-9196-66f4c47ac868"

echo "=== Konfiguracja Microsoft Graph API w Microsoft Entra ID ==="

echo "1. Pobieranie Tenant ID..."
TENANT_ID=$(az account show --query tenantId -o tsv)
echo "Tenant ID: $TENANT_ID"

echo "2. Sprawdzanie czy aplikacja '$APP_NAME' już istnieje..."
EXISTING_APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv)

if [ -n "$EXISTING_APP_ID" ]; then
    echo "Znaleziono istniejącą aplikację: $EXISTING_APP_ID"
    CLIENT_ID="$EXISTING_APP_ID"
else
    echo "Tworzenie nowej App Registration w Entra ID..."
    CLIENT_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
    echo "Utworzono aplikację o Client ID: $CLIENT_ID"
fi

echo "3. Sprawdzanie / tworzenie Service Principal..."
SP_ID=$(az ad sp list --filter "appId eq '$CLIENT_ID'" --query "[0].id" -o tsv)
if [ -z "$SP_ID" ]; then
    echo "Tworzenie Service Principal dla aplikacji..."
    az ad sp create --id "$CLIENT_ID" > /dev/null
fi

echo "4. Dodawanie uprawnienia Mail.Read (Application) do Microsoft Graph..."
az ad app permission add \
    --id "$CLIENT_ID" \
    --api "$GRAPH_API_ID" \
    --api-permissions "$MAIL_READ_ROLE_ID=Role" > /dev/null

echo "5. Udzielanie zgody administratora (Admin Consent)..."
az ad app permission admin-consent --id "$CLIENT_ID" || {
    echo "Ostrzeżenie: Nie udało się automatycznie nadać zgody administratora."
    echo "Upewnij się, że Twoje konto ma uprawnienia Global Administrator lub poproś admina o kliknięcie 'Grant admin consent' w portalu Azure."
}

echo "6. Generowanie nowego Client Secret..."
CLIENT_SECRET=$(az ad app credential reset --id "$CLIENT_ID" --append --display-name "lex-agent-secret" --query password -o tsv)

echo ""
echo "=== KONFIGURACJA ZAKOŃCZONA POMYŚLNIE ==="
echo "Skopiuj i dodaj poniższe wartości do pliku .env:"
echo "---------------------------------------------------------"
echo "AZURE_TENANT_ID=\"$TENANT_ID\""
echo "AZURE_CLIENT_ID=\"$CLIENT_ID\""
echo "AZURE_CLIENT_SECRET=\"$CLIENT_SECRET\""
echo "MS_GRAPH_MAILBOX_USER=\"twoja-skrzynka@domena.pl\""
echo "---------------------------------------------------------"
