import os
from typing import Protocol
import httpx
from src.core.decorators import http_retry, log_execution

SLACK_WEBHOOK_URL_ENV = "SLACK_WEBHOOK_URL"


class SlackService(Protocol):
    """Protocol interface for sending Slack notifications."""

    async def send_message(self, message: str) -> str:
        """Sends a notification message to Slack."""
        ...


class SlackWebhookService:
    """Implementation of SlackService using Incoming Webhooks."""

    def __init__(self, client: httpx.AsyncClient, webhook_url: str | None = None) -> None:
        self.client = client
        self.webhook_url = webhook_url or os.getenv(SLACK_WEBHOOK_URL_ENV, "")

    def __str__(self) -> str:
        return "SlackWebhookService(Incoming Webhook Client)"

    def __repr__(self) -> str:
        return f"SlackWebhookService(configured={bool(self.webhook_url)})"

    @log_execution()
    @http_retry
    async def send_message(self, message: str) -> str:
        """Sends a payload to the configured Slack webhook URL."""
        if not self.webhook_url:
            return "Slack notification skipped: SLACK_WEBHOOK_URL is not configured."

        payload = {"text": message}
        response = await self.client.post(self.webhook_url, json=payload)
        response.raise_for_status()
        return "Notification successfully sent to Slack."
