from src.infrastructure.database.db import get_postgres_connection
from src.infrastructure.services.web_search_service import WebService, TavilySearchService
from src.infrastructure.services.slack_service import SlackService, SlackWebhookService
from src.infrastructure.email.ms_graph_client import EmailService, MSGraphEmailClient
from src.infrastructure.blob.client import upload_document_to_blob

from src.rag.parsers.pdf_extractor import extract_text_from_pdf_file
from src.rag.retrievers.hybrid_retriever import HybridLegalRetriever, format_rag_context

from src.core.decorators import log_execution
from langchain_core.tools import tool, BaseTool
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
import httpx
from pathlib import Path


_embeddings = NVIDIAEmbeddings()

SEARCH_QUERY = """
    SELECT id, title, blob_url, 1 - (embedding <=> $1::vector) AS similarity
    FROM legal_documents
    ORDER BY embedding <=> $1::vector
    LIMIT 5;
"""
INSERT_DOCUMENT_QUERY = """
    INSERT INTO legal_documents (title, blob_url, document_type, embedding)
    VALUES ($1, $2, $3, $4::vector)
    RETURNING id;
"""
ATTACHMENTS_DIR = Path("downloads/attachments")


@tool(_handle_tool_error=True)
@log_execution()
def extract_text_from_pdf_tool(file_path: str) -> str:
    """Extracts raw text content from a local PDF document located at the given path."""
    return extract_text_from_pdf_file(file_path)


@tool(_handle_tool_error=True)
@log_execution()
async def search_legal_database_tool(query: str, top_k: int = 5) -> str:
    """Searches indexed legal acts and statutory articles using hybrid dense and sparse retrieval with RRF."""
    retriever = HybridLegalRetriever()
    results = await retriever.search_hybrid(query=query, top_k=top_k)
    return format_rag_context(results)


@tool(_handle_tool_error=True)
@log_execution()
async def download_court_case_document_tool(case_signature: str) -> str:
    """Downloads a court case document PDF from the legal portal via automated headless RPA with 2FA and saves it."""
    from src.rpa.browser.portal_automation import LegalPortalAutomation

    automation = LegalPortalAutomation()
    blob_url = await automation.fetch_and_archive_case(case_signature)
    return f"Dokument sprawy {case_signature} zostal pomyslnie pobrany i zarchiwizowany w chmurze Azure Blob: {blob_url}"


@tool(_handle_tool_error=True)
@log_execution()
async def search_postgres_database_tool(search_term: str) -> list | str:
    """
    Searches the PostgreSQL database using vector search (pgvector).
    Embeds the search term and uses cosine similarity to find the most relevant documents.
    """
    query_vector = await _embeddings.aembed_query(search_term)
    vector_str = "[" + ",".join(map(str, query_vector)) + "]"

    async with get_postgres_connection(readonly=True) as conn:
        rows = await conn.fetch(SEARCH_QUERY, vector_str)

    return [{**dict(r), "id": str(r["id"])} for r in rows]


@tool(_handle_tool_error=True)
@log_execution()
async def save_opinion_to_drive_tool(
    file_name: str,
    content: str,
    document_type: str = "legal_opinion",
) -> str:
    """
    Saves a generated legal opinion or document to Azure Blob Storage.
    Returns the URL of the uploaded blob.
    """
    blob_url = await upload_document_to_blob(blob_name=file_name, data=content)

    query_vector = await _embeddings.aembed_query(content)
    vector_str = "[" + ",".join(map(str, query_vector)) + "]"

    async with get_postgres_connection(readonly=False) as conn:
        doc_id = await conn.fetchval(
            INSERT_DOCUMENT_QUERY,
            file_name,
            blob_url,
            document_type,
            vector_str,
        )

    return f"Document saved to Blob Storage ({blob_url}) and indexed in database with ID: {doc_id}"


def create_download_email_attachment_tool(email_service: EmailService) -> BaseTool:
    """Factory creating download_email_attachment_tool with injected EmailService."""

    @tool(_handle_tool_error=True)
    @log_execution()
    async def download_email_attachment_tool(subject_filter: str | None = None) -> dict | str:
        """
        Downloads the latest email attachment from Microsoft 365 inbox via Microsoft Graph API.
        Saves the file locally and returns attachment metadata with the local file path.
        """
        attachment = await email_service.get_latest_attachment(subject_filter=subject_filter)
        if not attachment:
            return "No matching email with attachment found in inbox."

        ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = ATTACHMENTS_DIR / attachment.filename
        file_path.write_bytes(attachment.content_bytes)

        return {
            "filename": attachment.filename,
            "file_path": str(file_path),
            "size": attachment.size,
            "subject": attachment.subject,
            "sender": attachment.sender,
        }

    return download_email_attachment_tool


def create_send_slack_notification_tool(slack_service: SlackService) -> BaseTool:
    """Factory creating send_slack_notification_tool with injected SlackService."""

    @tool(_handle_tool_error=True)
    @log_execution()
    async def send_slack_notification_tool(message: str) -> str:
        """Sends a notification or alert to a dedicated Slack channel via webhook."""
        return await slack_service.send_message(message)

    return send_slack_notification_tool


def create_search_web_tool(search_service: WebService) -> BaseTool:
    """Factory creating search_web_tool with injected WebService."""

    @tool(_handle_tool_error=True)
    @log_execution()
    async def search_web_tool(query: str) -> str:
        """
        Searches the web using Tavily API for general knowledge, news, and external information.
        Useful when the Agent needs to find information outside of the internal database.
        """
        return await search_service(query)

    return search_web_tool


def create_agent_tools(
    search_service: WebService | None = None,
    slack_service: SlackService | None = None,
    email_service: EmailService | None = None,
) -> list[BaseTool]:
    """Creates full list of agent tools with injected dependencies or defaults."""
    default_client = None
    if not (search_service and slack_service and email_service):
        default_client = httpx.AsyncClient(timeout=15.0)

    web_svc = search_service or TavilySearchService(client=default_client, max_results=3)
    slack_svc = slack_service or SlackWebhookService(client=default_client)
    email_svc = email_service or MSGraphEmailClient(client=default_client)

    return [
        create_search_web_tool(web_svc),
        create_send_slack_notification_tool(slack_svc),
        create_download_email_attachment_tool(email_svc),
        search_postgres_database_tool,
        save_opinion_to_drive_tool,
        extract_text_from_pdf_tool,
        search_legal_database_tool,
        download_court_case_document_tool,
    ]


download_email_attachment_tool = create_download_email_attachment_tool(
    MSGraphEmailClient(client=httpx.AsyncClient(timeout=20.0))
)
send_slack_notification_tool = create_send_slack_notification_tool(
    SlackWebhookService(client=httpx.AsyncClient(timeout=10.0))
)
search_web_tool = create_search_web_tool(
    TavilySearchService(client=httpx.AsyncClient(timeout=15.0), max_results=3)
)