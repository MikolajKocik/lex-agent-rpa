#!/bin/bash
set -e

RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-lex-rpa-agent}"
STORAGE_ACCOUNT="${AZURE_STORAGE_ACCOUNT:-lexrpaagentstorage}"

echo "Pobieranie ID aktualnie zalogowanego użytkownika z Azure CLI..."
USER_ID=$(az ad signed-in-user show --query id -o tsv | tr -d '\r')

if [ -z "$USER_ID" ]; then
    echo "Błąd: Nie udało się pobrać ID użytkownika. Upewnij się, że jesteś zalogowany ('az login')."
    exit 1
fi

echo "Użytkownik ID: $USER_ID"

echo "Pobieranie ID konta Storage Account ($STORAGE_ACCOUNT)..."
STORAGE_ID=$(az storage account show \
    --name "$STORAGE_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --query id -o tsv | tr -d '\r')

if [ -z "$STORAGE_ID" ]; then
    echo "Błąd: Nie znaleziono konta magazynu $STORAGE_ACCOUNT w grupie $RESOURCE_GROUP."
    exit 1
fi

echo "Nadawanie roli 'Storage Blob Data Contributor'..."
az role assignment create \
    --role "Storage Blob Data Contributor" \
    --assignee "$USER_ID" \
    --scope "$STORAGE_ID"

echo ""
echo "Uprawnienia RBAC do Blob Storage zostały pomyślnie nadane!"
echo "Pamiętaj, że propagacja uprawnień RBAC w Azure może zająć 1-2 minuty."
