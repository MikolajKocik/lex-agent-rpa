from uuid import uuid4
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from src.core.decorators import log_execution
from src.api.schemas import (
    AgentRequest,
    AgentResponse,
    AsyncTaskResponse,
    TaskStatusResponse,
)
from src.api.dependencies import get_graph_service
from src.infrastructure.services.agent_service import GraphService

router = APIRouter(tags=["Agent"])

_TASK_STORE: dict[str, dict[str, str | None]] = {}


async def _run_background_agent_task(
    task_id: str,
    question: str,
    context: dict,
    graph_service: GraphService,
) -> None:
    """Executes agent workflow as an asynchronous background worker and records results."""
    try:
        result = await graph_service(question, context=context)
        _TASK_STORE[task_id] = {
            "status": "completed",
            "result": result,
            "error": None,
        }
    except Exception as exc:
        _TASK_STORE[task_id] = {
            "status": "failed",
            "result": None,
            "error": str(exc),
        }


@router.post("/task", response_model=AgentResponse, status_code=status.HTTP_200_OK)
@log_execution()
async def execute_agent_task(
    payload: AgentRequest,
    graph_service: GraphService = Depends(get_graph_service),
) -> AgentResponse:
    """
    Main entry point for synchronous execution.
    Receives the goal/task (e.g., 'Analyze contract X and check GDPR compliance').
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


@router.post("/task/async", response_model=AsyncTaskResponse, status_code=status.HTTP_202_ACCEPTED)
@log_execution()
async def execute_agent_task_async(
    payload: AgentRequest,
    background_tasks: BackgroundTasks,
    graph_service: GraphService = Depends(get_graph_service),
) -> AsyncTaskResponse:
    """Queues the agent legal analysis task for asynchronous background execution."""
    task_id = str(uuid4())
    context = {}
    if payload.document_content:
        context["document_content"] = payload.document_content

    _TASK_STORE[task_id] = {
        "status": "processing",
        "result": None,
        "error": None,
    }

    background_tasks.add_task(
        _run_background_agent_task,
        task_id,
        payload.question,
        context,
        graph_service,
    )

    return AsyncTaskResponse(
        task_id=task_id,
        status="processing",
        message="Task queued for background execution",
    )


@router.get("/task/{task_id}", response_model=TaskStatusResponse, status_code=status.HTTP_200_OK)
def get_task_status(task_id: str) -> TaskStatusResponse:
    """Fetches the current processing status or result of a queued background agent task."""
    task_data = _TASK_STORE.get(task_id)
    if not task_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found.",
        )

    return TaskStatusResponse(
        task_id=task_id,
        status=task_data["status"] or "unknown",
        result=task_data.get("result"),
        error=task_data.get("error"),
    )


@router.get("/health", status_code=status.HTTP_200_OK)
def healthcheck() -> dict[str, str]:
    """Healthcheck endpoint for monitoring service status."""
    return {"status": "ok"}

