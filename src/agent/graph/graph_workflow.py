from agent.graph import (
    route_after_rpa,
    route_after_critic,
    route_after_audit,
)
from dataclasses import dataclass
from .graph_nodes import (
    automate_web_process_node,
    ground_review_node,
    critical_review_node,
    audit_lex_node,
    critical_secure_node
)
from .graph_states import AgentState

from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime

@dataclass
class Context:
    user_id: str

# TODO use thread_id from Runtime and Context for user_id
workflow = StateGraph(AgentState)

# register nodes
workflow.add_node("rpa_executor", automate_web_process_node)
workflow.add_node("ground_review", ground_review_node)
workflow.add_node("critical_review", critical_review_node)
workflow.add_node("security_audit", audit_lex_node)
workflow.add_node("final_review", critical_secure_node)

# graph flow
workflow.add_edge(START, "rpa_executor")
#workflow.add_edge("rpa_executor", "ground_review")

# TODO Jeśli umowa znaleziona -> idź do Ground Review. | Jeśli brak umowy -> idź do END (koniec programu).
workflow.add_conditional_edges(
    "rpa_executor", 
    route_after_rpa 
)

workflow.add_edge("ground_review", "critical_review")

# TODO Krytyk decyduje: "Muszę sprawdzić RODO" -> warunek kieruje go do węzła z Narzędziem.
# TODO Narzędzie pobiera dane z internetu -> warunek kieruje go z powrotem do Krytyka.
# TODO Krytyk czyta dane z internetu i mówi: "Gotowe, piszę opinię" -> warunek wypuszcza go dalej do Audytu Bezpieczeństwa.
workflow.add_conditional_edges(
    "critical_review",
    route_after_critic
)

# TODO Jeśli is_safe == True -> idź do Ostatecznego Krytyka. | Jeśli is_safe == False -> idź do END i wyślij alarm na Slacka (odrzucamy dokument) 
workflow.add_conditional_edges(
    "security_audit",
    route_after_audit
)

workflow.add_edge("final_review", END)

agent_app = workflow.compile()
