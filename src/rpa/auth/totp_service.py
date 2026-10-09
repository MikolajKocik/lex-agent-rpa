import logging
import os

import pyotp

from src.infrastructure.keyvault.client import secret_client

logger = logging.getLogger(__name__)


class TOTPAuthService:
    """Manages generation and validation of 2FA TOTP passcodes using secrets from Azure Key Vault."""

    def __init__(
        self,
        secret_name: str = "Portal2FASecret",
        fallback_secret: str | None = None,
    ) -> None:
        self._secret_name = secret_name
        self._fallback_secret = fallback_secret or os.getenv("PORTAL_2FA_SECRET")

    def get_totp_secret(self) -> str:
        """Retrieves the Base32 2FA secret from Azure Key Vault with environment variable fallback."""
        try:
            secret = secret_client.get_secret(self._secret_name).value
            if secret:
                return secret
        except Exception as exc:
            logger.warning(
                f"Failed to fetch 2FA secret '{self._secret_name}' from Key Vault: {exc}. "
                "Attempting fallback secret."
            )

        if self._fallback_secret:
            return self._fallback_secret

        raise ValueError(
            f"TOTP secret not found in Azure Key Vault under '{self._secret_name}' "
            "and no fallback secret provided."
        )

    def generate_current_totp(self) -> str:
        """Generates the current 6-digit Time-Based One-Time Password."""
        secret = self.get_totp_secret()
        totp = pyotp.TOTP(secret)
        return totp.now()

    def verify_totp(self, code: str) -> bool:
        """Verifies if the supplied passcode matches current or adjacent TOTP intervals."""
        secret = self.get_totp_secret()
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
