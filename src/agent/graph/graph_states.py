from typing import Annotated, Any, TypedDict
import operator

from langchain_core.documents.base import Document
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

# agent for analyse and review lex content (docs, archives...)
class GroundReviewState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    extracted_clauses: list[str]
    identified_risks: list[str]

# agent for secure legal articles and vurnelable data
class SecurityLexState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    pii_entities_found: list[str]
    is_safe: bool

# agent as layer actor who define his opinion due to law
class CriticAnalyzeState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    doc: Document | None 
    content: str | None
    legal_opinion: str

# inteligent agent for scratch and automate web processes
class RpaExecutorState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    actions_completed: Annotated[list[str], operator.add]
    final_report_path: str | None

# supervisor agent
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    input_task: str
    generation: str

    # sub-processes
    ground_review_result: dict[str, Any]
    security_audit_result: dict[str, Any]
    security_check_status: bool
    critic_opinion: str
    rpa_status: str
