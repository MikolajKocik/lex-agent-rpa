#!/bin/bash
set -e

VAULT_NAME="${AZURE_KEYVAULT_NAME:-lex-rpa-keyvault}"

echo "=== Konfiguracja sekretów w Azure Key Vault: $VAULT_NAME ==="

read -s -p "1. Podaj hasło do PostgreSQL (PostgresPassword): " POSTGRES_PASS
echo ""
read -s -p "2. Podaj klucz API Tavily (TavilyApiKey): " TAVILY_KEY
echo ""
read -s -p "3. Podaj klucz API NVIDIA (NvidiaApiKey) [opcjonalnie, Enter aby pominąć]: " NVIDIA_KEY
echo ""

if [ -n "$POSTGRES_PASS" ]; then
    echo "Zapisywanie PostgresPassword w Key Vault..."
    az keyvault secret set --vault-name "$VAULT_NAME" --name "PostgresPassword" --value "$POSTGRES_PASS" > /dev/null
    echo "PostgresPassword zapisany."
fi

if [ -n "$TAVILY_KEY" ]; then
    echo "Zapisywanie TavilyApiKey w Key Vault..."
    az keyvault secret set --vault-name "$VAULT_NAME" --name "TavilyApiKey" --value "$TAVILY_KEY" > /dev/null
    echo "TavilyApiKey zapisany."
fi

if [ -n "$NVIDIA_KEY" ]; then
    echo "Zapisywanie NvidiaApiKey w Key Vault..."
    az keyvault secret set --vault-name "$VAULT_NAME" --name "NvidiaApiKey" --value "$NVIDIA_KEY" > /dev/null
    echo "NvidiaApiKey zapisany."
fi

echo ""
echo "Wszystkie sekrety zostały pomyślnie zaktualizowane w Key Vault ($VAULT_NAME)!"
