from unittest.mock import MagicMock, patch

from src.agent.graph.graph_nodes import (
    audit_lex_node,
    automate_web_process_node,
    ground_review_node,
)
from src.agent.graph.graph_states import AgentState
from src.agent.graph.route_nodes import (
    route_after_audit,
    route_after_critic,
    route_after_rpa,
)
from src.core.models import GroundReviewResponse, SecurityLexResponse


def test_route_after_rpa_success() -> None:
    state: AgentState = {
        "rpa_status": "success",
        "document_content": "Treść umowy najmu lokalu użytkowego.",
        "input_task": "Zbadaj umowę",
        "messages": [],
    }
    decision = route_after_rpa(state)
    assert decision == "ground_review"


def test_route_after_rpa_failure() -> None:
    state: AgentState = {
        "rpa_status": "error",
        "document_content": "",
        "input_task": "Zbadaj umowę",
        "messages": [],
    }
    decision = route_after_rpa(state)
    assert decision == "notify_slack_error"


def test_route_after_critic_needs_research() -> None:
    state: AgentState = {
        "needs_external_research": True,
        "input_task": "Sprawdź orzecznictwo RODO",
        "messages": [],
    }
    decision = route_after_critic(state)
    assert decision == "web_research_node"


def test_route_after_critic_proceeds_to_audit() -> None:
    state: AgentState = {
        "needs_external_research": False,
        "input_task": "Standardowa analiza",
        "messages": [],
    }
    decision = route_after_critic(state)
    assert decision == "security_audit"


def test_route_after_audit_safe() -> None:
    state: AgentState = {
        "security_check_status": True,
        "input_task": "Zadanie",
        "messages": [],
    }
    decision = route_after_audit(state)
    assert decision == "final_review"


def test_route_after_audit_rejected() -> None:
    state: AgentState = {
        "security_check_status": False,
        "input_task": "Zadanie",
        "messages": [],
    }
    decision = route_after_audit(state)
    assert decision == "reject_and_notify_slack"


def test_automate_web_process_node_success() -> None:
    state: AgentState = {
        "document_content": "Umowa o poufności NDA",
        "input_task": "Przeanalizuj",
        "messages": [],
    }
    result = automate_web_process_node(state)
    assert result["rpa_status"] == "success"
    assert result["document_content"] == "Umowa o poufności NDA"


def test_automate_web_process_node_empty() -> None:
    state: AgentState = {
        "document_content": "",
        "input_task": "",
        "messages": [],
    }
    result = automate_web_process_node(state)
    assert result["rpa_status"] == "error"
    assert "No document content" in result["error_message"]


@patch("src.agent.graph.graph_nodes.llm")
def test_ground_review_node_with_mock_llm(mock_llm: MagicMock) -> None:
    mock_chain = MagicMock()
    mock_response = GroundReviewResponse(
        extracted_clauses=["§ 1 Poufność", "§ 2 Kary"],
        identified_risks=["Brak limitu kar umownych"],
    )
    mock_chain.invoke.return_value = mock_response
    mock_llm.with_structured_output.return_value = mock_llm

    with patch("src.agent.graph.graph_nodes.load_prompt") as mock_load_prompt:
        mock_prompt = MagicMock()
        mock_prompt.__or__.return_value = mock_chain
        mock_load_prompt.return_value = mock_prompt

        state: AgentState = {
            "document_content": "Treść umowy testowej",
            "input_task": "Wyciągnij klauzule",
            "messages": [],
        }
        result = ground_review_node(state)

        assert "ground_review_result" in result
        assert result["ground_review_result"]["extracted_clauses"] == ["§ 1 Poufność", "§ 2 Kary"]
        assert result["ground_review_result"]["identified_risks"] == ["Brak limitu kar umownych"]


@patch("src.agent.graph.graph_nodes.llm")
def test_audit_lex_node_with_mock_llm(mock_llm: MagicMock) -> None:
    mock_chain = MagicMock()
    mock_response = SecurityLexResponse(
        is_safe=True,
        pii_entities_found=[],
        security_summary="Dokument bezpieczny, brak PII.",
    )
    mock_chain.invoke.return_value = mock_response
    mock_llm.with_structured_output.return_value = mock_llm

    with patch("src.agent.graph.graph_nodes.load_prompt") as mock_load_prompt:
        mock_prompt = MagicMock()
        mock_prompt.__or__.return_value = mock_chain
        mock_load_prompt.return_value = mock_prompt

        state: AgentState = {
            "document_content": "Umowa zanonimizowana",
            "input_task": "Audyt PII",
            "messages": [],
        }
        result = audit_lex_node(state)

        assert result["security_check_status"] is True
        assert result["security_audit_result"]["is_safe"] is True
        assert result["security_audit_result"]["pii_entities_found"] == []
