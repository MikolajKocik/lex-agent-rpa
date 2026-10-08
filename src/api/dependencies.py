from fastapi import Request
import httpx
from nemoguardrails import Guardrails

from infrastructure.services.agent_services import GraphService

def get_guardrails(request: Request) -> Guardrails:
    """Returns initialized guardrails instance from app state."""
    return request.app.state.rails

def get_http_client(request: Request) -> httpx.AsyncClient:
    """Returns async HTTP client from app state."""
    return request.app.state.http_client

def get_graph_service(request: Request) -> GraphService:
    """Returns initialized GraphService."""
    return GraphService(rails=request.app.state.rails)
