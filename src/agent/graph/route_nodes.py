from agent.graph.graph_states import AgentState


def route_after_rpa(state: AgentState) -> str:
    """Decides whether the document was downloaded successfully by the RPA worker."""
    if state.get("rpa_status") == "success" and state.get("document_content"):
        return "ground_review"
    return "notify_slack_error"


def route_after_critic(state: AgentState) -> str:
    """Decides whether the Critic requires external web search or can proceed to audit."""
    if state.get("needs_external_research", False):
        return "web_research_node"
    return "security_audit"


def route_after_audit(state: AgentState) -> str:
    """Decides the next step based on the security compliance and PII audit."""
    if state.get("security_check_status", True):
        return "final_review"
    return "reject_and_notify_slack"