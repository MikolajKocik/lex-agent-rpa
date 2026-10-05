from nemoguardrails.actions import action
from langdetect import detect

import logging

log = logging.getLogger(__name__)

@action(name="check_polish_language_action")
async def check_polish_language_action(bot_response: str) -> bool:
    """
    Verify, whether the response is generated in polish as native or not.
    
    Returns:
        bool: True (if polish), False (other language).
    """
    if not bot_response or not bot_response.strip():
        return True 
        
    try:        
        lang = detect(bot_response)
        return lang == 'pl'
    except ImportError:
        log.error("Library 'langdetect' not found")
        return True 
    except Exception as e:
        log.warning(f"Nie udało się wykryć języka: {e}")
        return True