from dataclasses import dataclass

from langgraph.graph import END, START, StateGraph

from .graph_nodes import (
    audit_lex_node,
    automate_web_process_node,
    critical_review_node,
    critical_secure_node,
    ground_review_node,
    notify_slack_error,
    reject_and_notify_slack,
    web_research_node,
)
from .graph_states import AgentState
from .route_nodes import (
    route_after_audit,
    route_after_critic,
    route_after_rpa,
)


@dataclass
class Context:
    """Execution context for graph sessions."""
    user_id: str


workflow = StateGraph(AgentState)

workflow.add_node("rpa_executor", automate_web_process_node)
workflow.add_node("ground_review", ground_review_node)
workflow.add_node("critical_review", critical_review_node)
workflow.add_node("web_research_node", web_research_node)
workflow.add_node("security_audit", audit_lex_node)
workflow.add_node("final_review", critical_secure_node)
workflow.add_node("reject_and_notify_slack", reject_and_notify_slack)
workflow.add_node("notify_slack_error", notify_slack_error)

workflow.add_edge(START, "rpa_executor")

workflow.add_conditional_edges(
    "rpa_executor",
    route_after_rpa,
    {
        "ground_review": "ground_review",
        "notify_slack_error": "notify_slack_error",
    },
)

workflow.add_edge("ground_review", "critical_review")

workflow.add_conditional_edges(
    "critical_review",
    route_after_critic,
    {
        "web_research_node": "web_research_node",
        "security_audit": "security_audit",
    },
)

workflow.add_edge("web_research_node", "critical_review")

workflow.add_conditional_edges(
    "security_audit",
    route_after_audit,
    {
        "final_review": "final_review",
        "reject_and_notify_slack": "reject_and_notify_slack",
    },
)

workflow.add_edge("final_review", END)
workflow.add_edge("reject_and_notify_slack", END)
workflow.add_edge("notify_slack_error", END)

agent_app = workflow.compile()
