from agent.graph.graph_states import AgentState
from langgraph.graph import END

def route_after_rpa(state: AgentState) -> str:
    """Decides whether the document was downloaded successfully."""
    # TODO: If rpa_status is an error, return END. If successful, return "ground_review"
    return "ground_review"

def route_after_critic(state: AgentState) -> str:
    """Decides whether the Critic needs to use a tool (e.g., DuckDuckGo)."""
    # TODO: Check if the LLM called a tool. If yes -> "tools", if no -> "security_audit"
    return "security_audit"

def route_after_audit(state: AgentState) -> str:
    """Decides the next step based on the security (PII) audit results."""
    # TODO: If the document is safe, go to "final_review", otherwise reject and return END
    return "final_review"