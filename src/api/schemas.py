from typing import Any
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.documents import Document

class AgentRequest(BaseModel):
    question: str = Field(min_length=10, description="User question provided as task to agent")

class AgentResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    answer: str = Field(description="Defines agent response")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata such as token usage, latency, or model name"
    )
    # agent nie zawsze musi uruchomić narzędzie - default=""
    trace: str = Field(
        default="", 
        description="Defines agent's trace for a tool invoked"
    )
    sources: list[Document] = Field(
        default_factory=list,
        description="List of documents which agent found for a provided task"
    )