import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.routers.agent import router as agent_router
from api.routers.search import router as search_router
from pathlib import Path

from nemoguardrails import Guardrails, RailsConfig
from nemoguardrails.actions import action

@action(is_system_action=True, name="run_langgraph_agent")
async def run_langgraph_agent(context: dict):
    """
    Main inference process defined using graph's states
    """
    user_message = context.get("last_user_message", "")

    # TODO: Replace the mock with actual LangGraph invocation
    # result = await graph.invoke({"messages": [user_message]})
    result = f"Agent result for: {user_message}"
    
    return result

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
