from fastapi import APIRouter, Depends
from api.schemas import AgentRequest, AgentResponse
from api.dependencies import get_graph_service

from infrastructure.services.agent_services import GraphService

router = APIRouter(tags=["Agent"])

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
    agent_result = await graph_service(payload.question)
    return AgentResponse(answer=agent_result)

@router.get("/health")
def healthcheck():
    return { "status": "ok" }
    
