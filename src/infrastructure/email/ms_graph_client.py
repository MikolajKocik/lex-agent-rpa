import base64
import os
from dataclasses import dataclass
from typing import Protocol

import httpx
from azure.identity.aio import DefaultAzureCredential

from src.core.decorators import http_retry, log_execution

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"


@dataclass
class EmailAttachment:
    """Represents a downloaded email attachment with metadata."""

    filename: str
    content_bytes: bytes
    content_type: str
    size: int
    message_id: str
    subject: str
    sender: str


class EmailService(Protocol):
    """Protocol for email and attachment retrieval."""

    async def get_latest_attachment(
        self,
        subject_filter: str | None = None,
    ) -> EmailAttachment | None:
        """Retrieves the latest attachment matching the optional subject filter."""
        ...


class MSGraphEmailClient:
    """Client for retrieving emails and attachments via Microsoft Graph API."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        mailbox: str | None = None,
        credential: DefaultAzureCredential | None = None,
    ) -> None:
        self.client = client
        self.mailbox = mailbox or os.getenv("MS_GRAPH_MAILBOX_USER", "me")
        self.credential = credential or DefaultAzureCredential()

    def __str__(self) -> str:
        return f"MSGraphEmailClient(mailbox={self.mailbox})"

    def __repr__(self) -> str:
        return f"MSGraphEmailClient(mailbox={self.mailbox})"

    async def _get_auth_headers(self) -> dict[str, str]:
        """Obtains an OAuth2 bearer token for Microsoft Graph from Azure Identity."""
        token = await self.credential.get_token(GRAPH_SCOPE)
        return {
            "Authorization": f"Bearer {token.token}",
            "Accept": "application/json",
        }

    @log_execution()
    @http_retry
    async def get_latest_attachment(
        self,
        subject_filter: str | None = None,
    ) -> EmailAttachment | None:
        """
        Fetches the latest email with attachments from the inbox
        and extracts the first file attachment.
        """
        headers = await self._get_auth_headers()
        endpoint_user = f"users/{self.mailbox}" if self.mailbox != "me" else "me"

        query_params = [
            "$filter=hasAttachments eq true",
            "$orderby=receivedDateTime desc",
            "$top=5",
        ]
        messages_url = f"{GRAPH_BASE_URL}/{endpoint_user}/mailFolders/Inbox/messages?{'&'.join(query_params)}"

        response = await self.client.get(messages_url, headers=headers)
        response.raise_for_status()
        messages = response.json().get("value", [])

        if not messages:
            return None

        target_message = None
        if subject_filter:
            for msg in messages:
                if subject_filter.lower() in msg.get("subject", "").lower():
                    target_message = msg
                    break
        else:
            target_message = messages[0]

        if not target_message:
            return None

        msg_id = target_message["id"]
        subject = target_message.get("subject", "")
        sender_info = target_message.get("from", {}).get("emailAddress", {})
        sender = sender_info.get("address", "")

        attachments_url = f"{GRAPH_BASE_URL}/{endpoint_user}/messages/{msg_id}/attachments"
        attach_response = await self.client.get(attachments_url, headers=headers)
        attach_response.raise_for_status()
        attachments = attach_response.json().get("value", [])

        for att in attachments:
            if att.get("@odata.type") == "#microsoft.graph.fileAttachment" and "contentBytes" in att:
                raw_bytes = base64.b64decode(att["contentBytes"])
                return EmailAttachment(
                    filename=att.get("name", "attachment.bin"),
                    content_bytes=raw_bytes,
                    content_type=att.get("contentType", "application/octet-stream"),
                    size=att.get("size", len(raw_bytes)),
                    message_id=msg_id,
                    subject=subject,
                    sender=sender,
                )


        return None
