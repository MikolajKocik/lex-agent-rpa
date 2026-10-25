import logging
import re

from nemoguardrails.actions import action

log = logging.getLogger(__name__)

_analyzer = None
_anonymizer = None


def _get_presidio():
    global _analyzer, _anonymizer
    if _analyzer is None:
        try:
            from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
            from presidio_anonymizer import AnonymizerEngine

            engine = AnalyzerEngine()
            pesel_pattern = Pattern(name="pesel_pattern", regex=r"\b\d{11}\b", score=0.5)
            pesel_recognizer = PatternRecognizer(
                supported_entity="PESEL",
                patterns=[pesel_pattern],
                context=["pesel", "nr pesel", "numer pesel"],
            )
            engine.registry.add_recognizer(pesel_recognizer)
            _analyzer = engine
            _anonymizer = AnonymizerEngine()
        except Exception as exc:
            log.warning("Could not initialize Presidio (%s). Using regex fallback.", exc)
            _analyzer = False
            _anonymizer = False
    return _analyzer, _anonymizer


def _fallback_mask(text: str) -> str:
    text = re.sub(r"\b\d{11}\b", "<PESEL>", text)
    text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "<EMAIL_ADDRESS>", text)
    text = re.sub(r"\b(?:\+48\s*)?(?:\d{3}[-\s]?){3}\b", "<PHONE_NUMBER>", text)
    return text


@action(name="mask_pii", is_system_action=False)
async def mask_pii(
    context: dict | None = None,
    source: str | None = None,
    text: str | None = None,
    **kwargs,
) -> dict | str:
    """
    Masks PII in the user message or text using Microsoft Presidio (with regex fallback).
    """
    ctx = context if isinstance(context, dict) else {}
    target_text = text or ctx.get("last_user_message", "")
    if not target_text:
        return {"last_user_message": ""} if context is not None else ""

    try:
        analyzer, anonymizer = _get_presidio()
        if analyzer and anonymizer:
            results = analyzer.analyze(
                text=target_text,
                entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "PESEL"],
                language="en",
            )
            anonymized_result = anonymizer.anonymize(text=target_text, analyzer_results=results)
            masked_text = anonymized_result.text
        else:
            masked_text = _fallback_mask(target_text)

        if masked_text != target_text:
            log.info("Masked PII. Original: '%s', Masked: '%s'", target_text, masked_text)

        if text is not None and context is None:
            return masked_text
        return {"last_user_message": masked_text}
    except Exception as e:
        log.error("Error in mask_pii: %s. Using fallback.", e)
        masked = _fallback_mask(target_text)
        return {"last_user_message": masked} if context is not None else masked
