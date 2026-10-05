from fastapi import FastAPI
from api.routes import router
from pathlib import Path

from nemoguardrails import Guardrails, RailsConfig
from nemoguardrails.actions import action

RAILS_PATH = str(Path(__file__).parent.parent / "agent" / "guardrails")

config = RailsConfig.from_path(RAILS_PATH)
rails = Guardrails(config)

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

rails.register_action(run_langgraph_agent)

app = FastAPI(
    title="RPA autonomous agent microservice",
    description="Manages an archive and legal documentation.",
    version="0.1.0"
)

app.state.rails = rails
app.include_router(router, prefix="/api")
