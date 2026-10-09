import pyotp
import pytest

from src.rpa.auth.totp_service import TOTPAuthService
from src.rpa.browser.portal_automation import (
    CaseNotFoundError,
    LegalPortalAutomation,
    PortalAuthenticationError,
    PortalAutomationError,
)


def test_totp_generation_and_verification() -> None:
    test_secret = pyotp.random_base32()
    service = TOTPAuthService(fallback_secret=test_secret)

    code = service.generate_current_totp()
    assert isinstance(code, str)
    assert len(code) == 6
    assert code.isdigit()

    assert service.verify_totp(code) is True
    assert service.verify_totp("999999") is False


def test_totp_service_raises_when_no_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PORTAL_2FA_SECRET", raising=False)
    service = TOTPAuthService(secret_name="NonExistentSecret12345", fallback_secret="")

    with pytest.raises(ValueError) as exc_info:
        service.get_totp_secret()

    assert "TOTP secret not found" in str(exc_info.value)



def test_legal_portal_automation_init() -> None:
    test_secret = pyotp.random_base32()
    totp_svc = TOTPAuthService(fallback_secret=test_secret)
    automation = LegalPortalAutomation(
        base_url="https://test.sad.gov.pl",
        totp_service=totp_svc,
        headless=True,
        timeout_ms=15000,
    )

    assert automation.base_url == "https://test.sad.gov.pl"
    assert automation.headless is True
    assert automation.timeout_ms == 15000
    assert automation.totp_service is totp_svc


def test_portal_exceptions_hierarchy() -> None:
    auth_err = PortalAuthenticationError("Invalid credentials")
    case_err = CaseNotFoundError("Signature not found")

    assert isinstance(auth_err, PortalAutomationError)
    assert isinstance(case_err, PortalAutomationError)
