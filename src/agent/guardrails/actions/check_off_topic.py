from nemoguardrails.actions import action
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
import logging

log = logging.getLogger(__name__)

@action(name="check_off_topic", is_system_action=False)
async def check_off_topic(context: dict) -> bool:
    """
    Checks if the user's input is off-topic (e.g., cooking recipes, weather, general chat).
    Returns True if the input is allowed (on-topic), False if it is off-topic.
    """
    user_message = context.get("last_user_message", "")
    if not user_message:
        return True
        
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0.0)
        messages = [
            SystemMessage(content="Jesteś strażnikiem (guardrail) systemu prawniczego. Twoim zadaniem jest ocena, czy poniższa wiadomość użytkownika jest 'off-topic' (czyli nie dotyczy prawa, dokumentów prawnych, procedur, umów, ani analizy biznesowej). Jeśli wiadomość dotyczy przepisów kulinarnych (np. szarlotki), pogody, dowcipów, lub luźnej rozmowy, odpowiedz tylko słowem YES. Jeśli dotyczy prawa lub analizy dokumentów, odpowiedz NO."),
            HumanMessage(content=user_message)
        ]
        
        response = await llm.ainvoke(messages)
        decision = response.content.strip().upper()
        
        if "YES" in decision:
            log.warning(f"Off-topic detected! Judge decision: {decision}")
            return False
            
        return True
    except Exception as e:
        log.error(f"Error during off-topic check: {e}")
        return True # Fallback to pass in case of API error
