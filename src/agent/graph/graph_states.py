import operator
from typing import Annotated, Any, TypedDict

from langchain_core.documents.base import Document
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class GroundReviewState(TypedDict):
    """Sub-state for ground analysis and legal risk identification."""
    messages: Annotated[list[AnyMessage], add_messages]
    extracted_clauses: list[str]
    identified_risks: list[str]


class SecurityLexState(TypedDict):
    """Sub-state for PII scanning and compliance security verification."""
    messages: Annotated[list[AnyMessage], add_messages]
    pii_entities_found: list[str]
    is_safe: bool


class CriticAnalyzeState(TypedDict):
    """Sub-state for critical review and legal opinion generation."""
    messages: Annotated[list[AnyMessage], add_messages]
    doc: Document | None
    content: str | None
    legal_opinion: str


class RpaExecutorState(TypedDict):
    """Sub-state for RPA document acquisition and process automation."""
    messages: Annotated[list[AnyMessage], add_messages]
    actions_completed: Annotated[list[str], operator.add]
    final_report_path: str | None


class AgentState(TypedDict):
    """Global workflow state governing the end-to-end legal analysis pipeline."""
    messages: Annotated[list[AnyMessage], add_messages]
    input_task: str
    generation: str

    document_content: str
    document_path: str | None
    rpa_status: str
    error_message: str | None

    ground_review_result: dict[str, Any]
    critic_opinion: str
    needs_external_research: bool
    research_query: str | None

    security_check_status: bool
    security_audit_result: dict[str, Any]
    slack_alert_sent: bool
