import os
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob import ContentSettings
from azure.storage.blob.aio import BlobServiceClient

ACCOUNT_URL = os.getenv(
    "AZURE_STORAGE_ACCOUNT_URL",
    "https://lexrpaagentstorage.blob.core.windows.net",
)
DEFAULT_CONTAINER = os.getenv(
    "AZURE_STORAGE_CONTAINER_NAME",
    "documents",
)


def get_blob_service_client() -> BlobServiceClient:
    """Creates and returns an asynchronous Azure Blob Service Client using DefaultAzureCredential."""
    credential = DefaultAzureCredential()
    return BlobServiceClient(account_url=ACCOUNT_URL, credential=credential)


async def upload_document_to_blob(
    blob_name: str,
    data: str | bytes,
    container_name: str = DEFAULT_CONTAINER,
    content_type: str | None = None,
) -> str:
    """Uploads document content to Azure Blob Storage and returns the blob URL."""
    async with get_blob_service_client() as client:
        container_client = client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        settings = ContentSettings(content_type=content_type) if content_type else None
        await blob_client.upload_blob(data, overwrite=True, content_settings=settings)
        return blob_client.url


async def download_document_from_blob(
    blob_name: str,
    container_name: str = DEFAULT_CONTAINER,
) -> bytes:
    """Downloads document content from Azure Blob Storage."""
    async with get_blob_service_client() as client:
        blob_client = client.get_blob_client(
            container=container_name, blob=blob_name
        )
        stream = await blob_client.download_blob()
        return await stream.readall()
