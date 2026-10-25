import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from nemoguardrails.actions import action

from src.agent.utils.agent_utils import load_prompt

log = logging.getLogger(__name__)

OFF_TOPIC_PROMPT = load_prompt(file_name="check_off_topic_prompt", version=1)


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
        chain = OFF_TOPIC_PROMPT | llm | StrOutputParser()

        result_text = await chain.ainvoke({"user_message": user_message})
        decision = result_text.strip().upper()

        if "YES" in decision:
            log.warning(f"Off-topic detected! Judge decision: {decision}")
            return False

        return True
    except Exception as e:
        log.error(f"Error during off-topic check: {e}")
        return True  # Fallback to pass in case of API error

