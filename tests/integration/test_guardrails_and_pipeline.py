import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agent.guardrails.actions.check_hallucination import check_hallucination_action
from src.agent.graph import agent_app


@pytest.mark.asyncio
async def test_hallucination_action_empty_inputs_returns_true() -> None:
    result = await check_hallucination_action(context={}, bot_response="")
    assert result is True


@pytest.mark.asyncio
@patch("src.agent.guardrails.actions.check_hallucination.ChatNVIDIA")
async def test_hallucination_action_detects_grounded_answer(mock_chat: AsyncMock) -> None:
    mock_instance = AsyncMock()
    mock_chat.return_value = mock_instance

    with patch("langchain_core.runnables.base.RunnableSequence.ainvoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = "NO"

        context = {"rag_context": "Art. 167 KP: Pracownik ma 4 dni urlopu na żądanie."}
        response = "Zgodnie z Kodeksem Pracy przysługują 4 dni urlopu na żądanie."

        decision = await check_hallucination_action(context=context, bot_response=response)
        assert decision is True


@pytest.mark.asyncio
@patch("src.agent.guardrails.actions.check_hallucination.ChatNVIDIA")
async def test_hallucination_action_blocks_hallucination(mock_chat: AsyncMock) -> None:
    mock_instance = AsyncMock()
    mock_chat.return_value = mock_instance

    with patch("langchain_core.runnables.base.RunnableSequence.ainvoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = "YES (Zawiera zmyślone informacje)"

        context = {"rag_context": "Art. 167 KP: Pracownik ma 4 dni urlopu na żądanie."}
        response = "Pracownik może wziąć 50 dni urlopu na żądanie w każdym miesiącu."

        decision = await check_hallucination_action(context=context, bot_response=response)
        assert decision is False


@pytest.mark.asyncio
async def test_agent_graph_executes_with_document_content() -> None:
    test_state = {
        "input_task": "Wyciągnij kluczowe klauzule z umowy",
        "document_content": "§ 1. Przedmiot umowy. Wykonawca wykona audyt.",
        "messages": [],
    }

    with patch("src.agent.graph.graph_nodes.llm") as mock_llm:
        from src.core.models import GroundReviewResponse, SecurityLexResponse, CriticAnalyzeResponse

        mock_ground = GroundReviewResponse(
            extracted_clauses=["§ 1 Przedmiot umowy"],
            identified_risks=[],
        )
        mock_audit = SecurityLexResponse(
            is_safe=True,
            pii_entities_found=[],
            security_summary="Brak PII.",
        )
        mock_critic = CriticAnalyzeResponse(
            legal_opinion="Umowa krótka i bezpieczna.",
            pii_summary="Brak wykrytych PII.",
        )


        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = [mock_ground, mock_critic, mock_audit, mock_critic]
        mock_llm.with_structured_output.return_value = mock_llm

        with patch("src.agent.graph.graph_nodes.load_prompt") as mock_prompt_loader:
            mock_prompt = MagicMock()
            mock_prompt.__or__.return_value = mock_chain
            mock_prompt_loader.return_value = mock_prompt


            final_state = await agent_app.ainvoke(test_state)

            assert final_state.get("rpa_status") == "success"
            assert "document_content" in final_state
