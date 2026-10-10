from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI

from nemoguardrails import Guardrails, RailsConfig
from nemoguardrails.actions import action
from nemoguardrails.llm.providers import register_chat_provider

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import ChatGoogleGenerativeAI

from src.agent.graph import agent_app
from src.api.routers.agent import router as agent_router
from src.api.routers.search import router as search_router


def _get_google_chat(**kwargs):
    return ChatGoogleGenerativeAI(**kwargs)

register_chat_provider("google", _get_google_chat)

@action(is_system_action=True, name="run_langgraph_agent")
async def run_langgraph_agent(context: dict):
    """Main inference process executing the LangGraph decision pipeline."""
    user_message = context.get("last_user_message", "")
    document_content = context.get("document_content", "")

    final_state = await agent_app.ainvoke({
        "input_task": user_message,
        "document_content": document_content,
        "messages": [],
    })

    return (
        final_state.get("critic_opinion")
        or final_state.get("generation")
        or "Zadanie zostało pomyślnie zrealizowane."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    rails_dir = Path(__file__).resolve().parent.parent / "agent" / "guardrails"
    if not rails_dir.exists():
        raise RuntimeError(
            f"Guardrails catalog does not exist or is not a directory: {rails_dir}"
        )
    
    config = RailsConfig.from_path(str(rails_dir))
    rails = Guardrails(config)
    rails.register_action(run_langgraph_agent)
    app.state.rails = rails

    limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
    timeout = httpx.Timeout(10.0, connect=5.0)

    app.state.http_client = httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        headers={"User-Agent": "FastAPI-Microservice/1.0"}
    )

    yield
    
    app.state.rails = None
    await app.state.http_client.aclose()


app = FastAPI(
    title="RPA autonomous agent microservice",
    description="Manages an archive and legal documentation.",
    version="0.1.0",
    lifespan=lifespan
)
app.include_router(agent_router, prefix="/api")
app.include_router(search_router, prefix="/api")
