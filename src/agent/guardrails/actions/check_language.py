from nemoguardrails.actions import action

@action(name="check_polish_language_action")
async def check_polish_language_action(bot_response: str) -> bool:
    """
    Weryfikuje, czy wygenerowana odpowiedź jest w języku polskim.
    
    Zwraca:
        bool: True (język polski), False (inny język).
    """
    pass