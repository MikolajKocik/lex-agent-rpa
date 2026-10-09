import pyotp
import pytest


@pytest.fixture(autouse=True)
def mock_azure_credentials(monkeypatch):
    """Automatically mock Azure credentials and secrets in CI/test environments to prevent network auth failures."""
    monkeypatch.setenv("AZURE_TENANT_ID", "test-tenant-id")
    monkeypatch.setenv("AZURE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_password")
    monkeypatch.setenv("TAVILY_API_KEY", "mock_tavily_key")
    monkeypatch.setenv("PORTAL_2FA_SECRET", pyotp.random_base32())

