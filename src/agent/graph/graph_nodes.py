from typing import cast
from src.agent.utils.agent_utils import load_prompt
from src.agent.tools import search_web_tool, send_slack_notification_tool
from .graph_states import AgentState

from src.core.config.llm_provider import NvidiaLLMProvider
from src.core.models import (
    GroundReviewResponse,
    SecurityLexResponse,
    CriticAnalyzeResponse,
)


nvidia_provider = NvidiaLLMProvider(temperature=0.1)
llm = nvidia_provider.model


def process_task_node(state: AgentState) -> dict:
    """Main node processing the query."""
    response = llm.invoke(state["input_task"])
    return {"generation": response.content}


def automate_web_process_node(state: AgentState) -> dict:
    """RPA Executor: Retrieves the document content and initializes workflow state."""
    doc_content = state.get("document_content") or state.get("input_task", "")
    if not doc_content:
        return {
            "rpa_status": "error",
            "error_message": "No document content or task input available for processing.",
        }

    return {
        "rpa_status": "success",
        "document_content": doc_content,
    }


def ground_review_node(state: AgentState) -> dict:
    """Ground Review: Basic analysis of facts and clauses from the document."""
    structured_llm = llm.with_structured_output(GroundReviewResponse)
    prompt = load_prompt(file_name="ground_reviewer_prompt", p_count=3, version=1)

    chain = prompt | structured_llm

    result = cast(
        GroundReviewResponse,
        chain.invoke({
            "document_content": state.get("document_content", ""),
            "input_task": state.get("input_task", ""),
        }),
    )
    return {"ground_review_result": result.model_dump()}


def critical_review_node(state: AgentState) -> dict:
    """Critical Review: Initial legal opinion and assessment of external research necessity."""
    task = state.get("input_task", "").lower()
    needs_research = ("rodo" in task or "gdpr" in task or "ustawa" in task) and not state.get("critic_opinion")

    if needs_research and not state.get("needs_external_research"):
        return {
            "needs_external_research": True,
            "research_query": state.get("input_task", "")[:120],
        }

    structured_llm = llm.with_structured_output(CriticAnalyzeResponse)
    prompt = load_prompt(file_name="critical_reviewer_prompt", p_count=3, version=1)

    chain = prompt | structured_llm

    ground_result = state.get("ground_review_result", {})
    extracted_clauses = "\n".join(ground_result.get("extracted_clauses", []))
    identified_risks = "\n".join(ground_result.get("identified_risks", []))

    result = cast(
        CriticAnalyzeResponse,
        chain.invoke({
            "extracted_clauses": extracted_clauses,
            "identified_risks": identified_risks,
            "input_task": state.get("input_task", ""),
        }),
    )
    return {
        "critic_opinion": result.legal_opinion,
        "needs_external_research": False,
    }


async def web_research_node(state: AgentState) -> dict:
    """Performs web research for legal precedents and statutory context."""
    query = state.get("research_query") or state.get("input_task", "")
    search_result = await search_web_tool.ainvoke(query)

    existing_opinion = state.get("critic_opinion", "")
    enriched_opinion = f"{existing_opinion}\n\n[Web Context]: {search_result}".strip()

    return {
        "critic_opinion": enriched_opinion,
        "needs_external_research": False,
    }


def audit_lex_node(state: AgentState) -> dict:
    """Security Audit: Checks for PII and compliance security."""
    structured_llm = llm.with_structured_output(SecurityLexResponse)
    prompt = load_prompt(file_name="security_audit_prompt", p_count=3, version=1)

    chain = prompt | structured_llm

    result = cast(
        SecurityLexResponse,
        chain.invoke({
            "document_content": state.get("document_content", "")
        }),
    )
    return {
        "security_check_status": result.is_safe,
        "security_audit_result": result.model_dump(),
    }


def critical_secure_node(state: AgentState) -> dict:
    """Final Review: Produces the ultimate legal opinion after security clearance."""
    structured_llm = llm.with_structured_output(CriticAnalyzeResponse)
    prompt = load_prompt(file_name="critical_secure_prompt", p_count=3, version=1)

    chain = prompt | structured_llm

    audit_result = state.get("security_audit_result", {})
    pii_summary = "\n".join(audit_result.get("pii_entities_found", []))
    if not pii_summary:
        pii_summary = "Brak znalezionych PII."

    result = cast(
        CriticAnalyzeResponse,
        chain.invoke({
            "preliminary_opinion": state.get("critic_opinion", ""),
            "pii_summary": pii_summary,
            "is_safe": str(state.get("security_check_status", True)),
            "input_task": state.get("input_task", ""),
        }),
    )
    return {"critic_opinion": result.legal_opinion}


async def reject_and_notify_slack(state: AgentState) -> dict:
    """Notifies compliance team of security audit failure and PII exposure."""
    audit = state.get("security_audit_result", {})
    pii_items = audit.get("pii_entities_found", [])
    message = (
        f"Security Alert: Document rejected due to PII compliance failure. "
        f"Detected entities: {', '.join(pii_items) if pii_items else 'Unspecified violations'}."
    )
    await send_slack_notification_tool.ainvoke(message)
    return {"slack_alert_sent": True}


async def notify_slack_error(state: AgentState) -> dict:
    """Notifies operations team of RPA execution failure."""
    error = state.get("error_message", "Unknown RPA processing failure")
    message = f"RPA Error: Document acquisition failed. Reason: {error}"
    await send_slack_notification_tool.ainvoke(message)
    return {"slack_alert_sent": True}