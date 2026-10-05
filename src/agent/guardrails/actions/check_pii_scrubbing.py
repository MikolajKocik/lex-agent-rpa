from nemoguardrails.actions import action

@action(name="scrub_pii")
async def scrub_pii_action(text: str) -> str:
    """
    Akcja maskująca dane wrażliwe (PII) w tekście.
    
    Argumenty:
        text (str): Tekst wejściowy (od użytkownika lub wygenerowany przez LLM).
        
    Zwraca:
        str: Tekst ze zmaskowanymi danymi (np. Jan Kowalski -> [OSOBA]).
    """
    # TODO: Implementacja PII scrubbing (np. za pomocą Microsoft Presidio)
    return text
