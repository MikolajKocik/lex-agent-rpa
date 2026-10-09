from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import sys
import logging

logger = logging.getLogger("azure")
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

credential = DefaultAzureCredential()

secret_client = SecretClient(
    vault_url="https://lex-rpa-keyvault.vault.azure.net/",
    credential=credential,
    logging_enable=True
)

logger.info("Getting a PostgresPassword secret from Key Vault...")
POSTGRES_PASSWORD = secret_client.get_secret("PostgresPassword").value

logger.info("Getting a TavilyApiKey secret from Key Vault...")
TAVILY_API_KEY = secret_client.get_secret("TavilyApiKey").value
