from pydantic import BaseModel, Field
from typing import Dict
from langchain_core.documents import Document

class AgentRequest(BaseModel):
    question: str = Field(min_length=10, description="User question provided as task to agent")

class AgentResponse(BaseModel):
    answer: str = Field(description="Defines agent response")
    metadata: Dict[str, str]
    trace: str = Field(description="Defines agent's trace for a tool invoked")
    sources: list[Document] = Field(description="List of documents which agent found for a provided task")