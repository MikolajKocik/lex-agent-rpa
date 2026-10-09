from typing import Any

from langchain_core.documents import Document
from pydantic import BaseModel, ConfigDict, Field


class AgentRequest(BaseModel):
    """Payload sent by the client to initiate an agent workflow."""
    question: str = Field(
        min_length=10,
        description="User question or goal provided as task to the agent",
    )
    document_content: str | None = Field(
        default=None,
        description="Optional raw document or contract text to be analyzed",
    )


class AgentResponse(BaseModel):
    """Response returned by the agent after workflow completion."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    answer: str = Field(description="Defines agent response")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata such as token usage, latency, or model name",
    )
    trace: str = Field(
        default="",
        description="Defines agent's trace for tools invoked during execution",
    )
    sources: list[Document] = Field(
        default_factory=list,
        description="List of source documents referenced by the agent",
    )


class AsyncTaskResponse(BaseModel):
    """Returned when a task is accepted for background execution."""

    task_id: str
    status: str = "queued"
    message: str = "Task queued for background execution"


class TaskStatusResponse(BaseModel):
    """Returned when querying the status of a background agent task."""

    task_id: str
    status: str
    result: str | None = None
    error: str | None = None