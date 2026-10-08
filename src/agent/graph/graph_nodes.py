from typing import cast
from langgraph.types import Command
from agent.utils.agent_utils import load_prompt
from .graph_states import AgentState

from core.config.llm_provider import NvidiaLLMProvider
from core.models import (
    GroundReviewResponse, 
    SecurityLexResponse, 
    CriticAnalyzeResponse, 
)

nvidia_provider = NvidiaLLMProvider(temperature=0.1)
llm = nvidia_provider.model  

def process_task_node(state: AgentState):
    """Main node processing the query."""
    response = llm.invoke(state["input_task"])
    return {"generation": response.content}

def automate_web_process_node(state: AgentState) -> dict:
    """RPA Executor: Downloads the file/data and starts the process."""

    # TODO Here would be the RPA logic downloading the file
    # update_state = Command(update=state["messages"])

    return {"rpa_status": "File downloaded and ready for review"}

def ground_review_node(state: AgentState) -> dict:
    """Ground Review: Basic analysis of facts from the document."""
    structured_llm = llm.with_structured_output(GroundReviewResponse)
    prompt = load_prompt(file_name="ground_reviewer_prompt", p_count=3, version=1)
    
    chain = prompt | structured_llm
    
    result = cast(GroundReviewResponse, chain.invoke({
        "document_content": "TUTAJ_TRESC_POBRANEJ_UMOWY", 
        "input_task": state.get("input_task", "")
    }))
    return {"ground_review_result": result.model_dump()}

def critical_review_node(state: AgentState) -> dict:
    """Critical Review: Initial legal opinion based on facts."""
    structured_llm = llm.with_structured_output(CriticAnalyzeResponse)
    prompt = load_prompt(file_name="critical_reviewer_prompt", p_count=3, version=1)
    
    chain = prompt | structured_llm
    
    ground_result = state.get("ground_review_result", {})
    extracted_clauses = "\n".join(ground_result.get("extracted_clauses", []))
    identified_risks = "\n".join(ground_result.get("identified_risks", []))
    
    result = cast(CriticAnalyzeResponse, chain.invoke({
        "extracted_clauses": extracted_clauses,
        "identified_risks": identified_risks,
        "input_task": state.get("input_task", "")
    }))
    return {"critic_opinion": result.legal_opinion}

def audit_lex_node(state: AgentState) -> dict:
    """Security Audit: Checks for PII and data security."""
    structured_llm = llm.with_structured_output(SecurityLexResponse)
    prompt = load_prompt(file_name="security_audit_prompt", p_count=3, version=1)
    
    chain = prompt | structured_llm
    
    result = cast(SecurityLexResponse, chain.invoke({
        "document_content": "TUTAJ_TRESC_POBRANEJ_UMOWY" 
    }))
    return {
        "security_check_status": result.is_safe,
        "security_audit_result": result.model_dump()
    }

def critical_secure_node(state: AgentState) -> dict:
    """Final Review: Ultimate legal opinion after the audit."""
    structured_llm = llm.with_structured_output(CriticAnalyzeResponse)
    prompt = load_prompt(file_name="critical_secure_prompt", p_count=3, version=1)
    
    chain = prompt | structured_llm
    
    audit_result = state.get("security_audit_result", {})
    pii_summary = "\n".join(audit_result.get("pii_entities_found", []))
    if not pii_summary:
        pii_summary = "Brak znalezionych PII."
    
    result = cast(CriticAnalyzeResponse, chain.invoke({
        "preliminary_opinion": state.get("critic_opinion", ""),
        "pii_summary": pii_summary,
        "is_safe": str(state.get("security_check_status", True)),
        "input_task": state.get("input_task", "")
    }))
    return {"critic_opinion": result.legal_opinion}