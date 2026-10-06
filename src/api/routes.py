from fastapi import APIRouter, Depends, Request
from .schemas import AgentRequest, AgentResponse

from infrastructure.services.agent_services import GraphService

router = APIRouter(tags=["Agent"])

# register dependency service
def get_graph_service(request: Request) -> GraphService:
    return GraphService(rails=request.app.state.rails)

@router.post("/task", response_model=AgentResponse)
async def execute_agent_task(
    payload: AgentRequest,
    graph_service: GraphService = Depends(get_graph_service)
):
    """
    Main entry point for the agent. Receives the goal/task (e.g., "Analyze contract X and move to archive Y").
    The agent decides in the background which Tools to use to execute the task.
    """
    # TODO update response with metadata from .schemas
    agent_result = await graph_service(payload.task)
    return AgentResponse(answer=agent_result)

@router.get("/health")
def healthcheck():
    return { "status": "ok" }
