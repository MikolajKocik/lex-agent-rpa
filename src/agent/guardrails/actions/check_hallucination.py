from nemoguardrails.actions import action

@action(name="check_hallucination_action")
async def check_hallucination_action(context: dict, bot_response: str) -> bool:
    """
    Sprawdza, czy odpowiedź bota jest poprawnie ugruntowana w kontekście RAG 
    i nie zawiera halucynacji.
    
    Zwraca:
        bool: True (brak halucynacji - przepuszczamy), False (wykryto halucynację - blokujemy).
    """
    pass