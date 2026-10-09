import logging
import os
from pathlib import Path

from playwright.async_api import Browser, Page, async_playwright

from src.infrastructure.blob.client import upload_document_to_blob
from src.rpa.auth.totp_service import TOTPAuthService

logger = logging.getLogger(__name__)


class PortalAutomationError(Exception):
    """Base exception for legal portal RPA automation failures."""


class PortalAuthenticationError(PortalAutomationError):
    """Raised when portal login or 2FA verification fails."""


class CaseNotFoundError(PortalAutomationError):
    """Raised when the requested case signature cannot be located on the portal."""



class LegalPortalAutomation:
    """Orchestrates headless browser automation for legal court portals with TOTP 2FA authentication."""

    def __init__(
        self,
        base_url: str | None = None,
        totp_service: TOTPAuthService | None = None,
        headless: bool = True,
        timeout_ms: int = 30000,
    ) -> None:
        self.base_url = base_url or os.getenv("LEGAL_PORTAL_URL", "https://portal.sad.gov.pl")
        self.totp_service = totp_service or TOTPAuthService()
        self.headless = headless
        self.timeout_ms = timeout_ms

    async def login_to_portal(
        self,
        page: Page,
        username: str,
        password: str,
        login_url: str | None = None,
    ) -> bool:
        """Fills login credentials, injects the generated TOTP 2FA code, and submits the authentication form."""
        target_url = login_url or f"{self.base_url}/login"
        await page.goto(target_url, timeout=self.timeout_ms, wait_until="domcontentloaded")

        captcha_element = await page.query_selector("iframe[src*='captcha'], div.g-recaptcha")
        if captcha_element:
            raise PortalAuthenticationError("Automated login blocked: CAPTCHA challenge detected on portal.")

        await page.fill("input[name='login'], input#username, input[type='email']", username)
        await page.fill("input[name='password'], input#password, input[type='password']", password)

        totp_field = await page.query_selector("input[name='totp'], input#otp, input[name='code']")
        if totp_field:
            totp_code = self.totp_service.generate_current_totp()
            await totp_field.fill(totp_code)

        await page.click("button[type='submit'], input[type='submit'], button#login-btn")
        await page.wait_for_load_state("networkidle")

        error_element = await page.query_selector(".alert-danger, .error-message, .login-error")
        if error_element:
            error_text = await error_element.inner_text()
            raise PortalAuthenticationError(f"Login failed on portal: {error_text.strip()}")

        return True

    async def download_case_document(
        self,
        case_signature: str,
        download_directory: Path | str = Path("downloads/court_cases"),
    ) -> Path:
        """Searches for a court case by its signature, downloads the judgment/docket PDF, and returns the file path."""
        out_dir = Path(download_directory)
        out_dir.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as playwright:
            browser: Browser = await playwright.chromium.launch(headless=self.headless)
            context = await browser.new_context(accept_downloads=True)
            page: Page = await context.new_page()

            try:
                username = os.getenv("PORTAL_USERNAME", "lex_agent_user")
                password = os.getenv("PORTAL_PASSWORD", "SecretPass123!")
                await self.login_to_portal(page, username=username, password=password)

                search_url = f"{self.base_url}/sprawy/szukaj"
                await page.goto(search_url, timeout=self.timeout_ms)

                search_input = await page.query_selector("input[name='signature'], input#search-signature")
                if not search_input:
                    raise CaseNotFoundError(f"Case search input not located on page {search_url}")

                await search_input.fill(case_signature)
                await page.click("button#search-btn, button[type='submit']")
                await page.wait_for_load_state("networkidle")

                download_link = await page.query_selector("a.download-document, a[href$='.pdf']")
                if not download_link:
                    raise CaseNotFoundError(f"Document for case signature '{case_signature}' not found.")

                async with page.expect_download() as download_info:
                    await download_link.click()

                download = await download_info.value
                sanitized_sig = case_signature.replace("/", "_").replace(" ", "_")
                target_path = out_dir / f"{sanitized_sig}.pdf"
                await download.save_as(target_path)

                return target_path

            finally:
                await browser.close()

    async def fetch_and_archive_case(
        self,
        case_signature: str,
        container_name: str = "documents",
    ) -> str:
        """Downloads case PDF via Playwright and archives it directly into Azure Blob Storage, returning the blob URL."""
        local_path = await self.download_case_document(case_signature)
        with open(local_path, "rb") as f:
            pdf_bytes = f.read()

        blob_name = f"court_cases/{local_path.name}"
        blob_url = await upload_document_to_blob(
            blob_name=blob_name,
            data=pdf_bytes,
            container_name=container_name,
            content_type="application/pdf",
        )
        return blob_url
