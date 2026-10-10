from nemoguardrails.actions import action


@action(name="check_jailbreak", is_system_action=False)
async def check_jailbreak(context: dict) -> bool:
    """
    Checks if the user's input contains a jailbreak attempt.
    Returns True if the input is safe, False if it is a jailbreak.
    """
    user_message = context.get("last_user_message", "")
    if not user_message:
        return True
        
    user_message_lower = user_message.lower()
    
    jailbreak_keywords = [
        "ignore previous instructions",
        "zapomnij poprzednie instrukcje",
        "system prompt",
        "you are no longer",
        "nie jesteś już",
        "bypass",
        "ominąć",
        "hack",
    ]
    
    for kw in jailbreak_keywords:
        if kw in user_message_lower:
            return False
            
    return True
