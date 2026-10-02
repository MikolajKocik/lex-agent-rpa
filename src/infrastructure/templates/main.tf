terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Reference existing Resource Group
data "azurerm_resource_group" "rg" {
  name = "lex-rpa-agent"
}

# Fetch current Azure client configuration
data "azurerm_client_config" "current" {}

# Provision Azure Key Vault
resource "azurerm_key_vault" "kv" {
  name                        = "lex-rpa-keyvault"
  location                    = "polandcentral" 
  resource_group_name         = data.azurerm_resource_group.rg.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"     

  # Retention policy on deletion
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false

  # Access policy for deployment principal
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Purge"
    ]
  }
}

# Provision Azure Storage Account
resource "azurerm_storage_account" "storage" {
  name                     = "lexrpaagentstorage"
  resource_group_name      = data.azurerm_resource_group.rg.name
  location                 = "polandcentral"
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# Provision Blob Storage container for document archives
resource "azurerm_storage_container" "blob" {
  name                  = "documents"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}
