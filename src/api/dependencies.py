import httpx
from fastapi import Depends, Request
from nemoguardrails import Guardrails

from src.agent.tools.agent_tools import create_agent_tools
from src.infrastructure.email.ms_graph_client import EmailService, MSGraphEmailClient
from src.infrastructure.services.agent_service import GraphService
from src.infrastructure.services.slack_service import SlackService, SlackWebhookService
from src.infrastructure.services.web_search_service import TavilySearchService, WebService


def get_guardrails(request: Request) -> Guardrails:
    """Returns initialized guardrails instance from app state."""
    return request.app.state.rails

def get_http_client(request: Request) -> httpx.AsyncClient:
    """Returns async HTTP client from app state."""
    return request.app.state.http_client

def get_graph_service(request: Request) -> GraphService:
    """Returns initialized GraphService."""
    return GraphService(rails=request.app.state.rails)

def get_web_search_service(
    client: httpx.AsyncClient = Depends(get_http_client),
) -> WebService:
    return TavilySearchService(client=client, max_results=5)

def get_slack_service(
    client: httpx.AsyncClient = Depends(get_http_client),
) -> SlackService:
    return SlackWebhookService(client=client)

def get_ms_graph_service(
    client: httpx.AsyncClient = Depends(get_http_client),
) -> EmailService:
    return MSGraphEmailClient(client=client)

def get_agent_tools(
    web_search_service: WebService = Depends(get_web_search_service),
    slack_service: SlackService = Depends(get_slack_service),
    email_service: EmailService = Depends(get_ms_graph_service),
):
    """Returns agent tools fully wired with FastAPI injected services."""
    return create_agent_tools(
        search_service=web_search_service,
        slack_service=slack_service,
        email_service=email_service,
    )
