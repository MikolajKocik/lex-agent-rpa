import logging

from nemoguardrails.actions import action
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine

log = logging.getLogger(__name__)

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

pesel_pattern = Pattern(name="pesel_pattern", regex=r"\b\d{11}\b", score=0.5)
pesel_recognizer = PatternRecognizer(
    supported_entity="PESEL", 
    patterns=[pesel_pattern], 
    context=["pesel", "nr pesel", "numer pesel"]
)
analyzer.registry.add_recognizer(pesel_recognizer)

@action(name="mask_pii", is_system_action=False)
async def mask_pii(context: dict) -> dict:
    """
    Masks PII in the user message using Microsoft Presidio.
    Returns a dict with the masked text to update the context.
    """
    user_message = context.get("last_user_message", "")
    if not user_message:
        return {"last_user_message": user_message}
        
    try:
        results = analyzer.analyze(
            text=user_message,
            entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "PESEL"],
            language="en" 
        )
        
        # text anonimization
        anonymized_result = anonymizer.anonymize(text=user_message, analyzer_results=results)
        masked_text = anonymized_result.text
        
        if masked_text != user_message:
            log.info(f"Masked PII in input. Original: '{user_message}', Masked: '{masked_text}'")
            
        return {"last_user_message": masked_text}
    except Exception as e:
        log.error(f"Error in mask_pii: {e}")
        return {"last_user_message": user_message}
