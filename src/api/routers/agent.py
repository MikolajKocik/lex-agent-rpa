from fastapi import APIRouter, Depends, HTTPException, status

from src.core.decorators import log_execution
from src.api.schemas import AgentRequest, AgentResponse
from src.api.dependencies import get_graph_service
from src.infrastructure.services.agent_service import GraphService

router = APIRouter(tags=["Agent"])


@router.post("/task", response_model=AgentResponse, status_code=status.HTTP_200_OK)
@log_execution()
async def execute_agent_task(
    payload: AgentRequest,
    graph_service: GraphService = Depends(get_graph_service),
) -> AgentResponse:
    """
    Main entry point for the agent.
    Receives the goal/task (e.g., "Analyze contract X and check GDPR compliance").
    Applies NeMo Guardrails, executes the LangGraph decision pipeline, and returns the legal analysis.
    """
    context = {}
    if payload.document_content:
        context["document_content"] = payload.document_content

    try:
        agent_result = await graph_service(payload.question, context=context)
        return AgentResponse(answer=agent_result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow execution failed: {exc}",
        ) from exc


@router.get("/health", status_code=status.HTTP_200_OK)
def healthcheck() -> dict[str, str]:
    """Healthcheck endpoint for monitoring service status."""
    return {"status": "ok"}
