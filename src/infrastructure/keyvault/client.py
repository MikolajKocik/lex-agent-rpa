import logging
import os
import sys

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger("azure")
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

VAULT_URL = os.getenv("AZURE_KEY_VAULT_URL", "https://lex-rpa-keyvault.vault.azure.net/")

try:
    credential = DefaultAzureCredential()
    secret_client = SecretClient(
        vault_url=VAULT_URL,
        credential=credential,
        logging_enable=True,
    )
except Exception as e:
    logger.warning("Failed to initialize Azure Key Vault SecretClient: %s", e)
    secret_client = None


def get_secret_with_fallback(secret_name: str, env_var: str, default: str = "") -> str:
    """Retrieves secret from Key Vault if available, otherwise falls back to environment variable."""
    env_val = os.getenv(env_var)
    if env_val:
        return env_val
    if secret_client:
        try:
            return secret_client.get_secret(secret_name).value
        except Exception as exc:
            logger.warning("Key Vault read failed for '%s': %s", secret_name, exc)
    return default


POSTGRES_PASSWORD = get_secret_with_fallback("PostgresPassword", "POSTGRES_PASSWORD", "test_password")
TAVILY_API_KEY = get_secret_with_fallback("TavilyApiKey", "TAVILY_API_KEY", "mock_tavily_key")

