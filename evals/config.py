"""
Konfiguracja ewaluacji RAG (parametry modeli, progi jakościowe, ścieżki).
"""

from pathlib import Path

EVALS_DIR = Path(__file__).parent.resolve()
DATA_DIR = EVALS_DIR / "data"
REPORTS_DIR = EVALS_DIR / "reports"

TEST_CASES_PATH = DATA_DIR / "test_cases.json"
UNANSWERABLE_PATH = DATA_DIR / "unanswerable.json"

URLS = [
    "https://www.gov.pl/web/sprawiedliwosc",
    "https://orzeczenia.ms.gov.pl/content/$N/154505000002503_VI_ACa_000676_2020_Uz_2021-09-29_001",
]

RAG_CONFIG = {
    "embedding_model": "models/gemini-embedding-001",
    "judge_embedding_model": "gemini-embedding-001",
    "chunk_size": 800,
    "chunk_overlap": 100,
    "top_k": 3,
    "generator_temperature": 0,
    "judge_model": "gemini-3.5-flash-lite",
}

RETRIEVAL_THRESHOLDS = {
    "context_precision_with_reference": 0.60,
    "context_recall": 0.70,
}

GENERATION_THRESHOLDS = {
    "faithfulness": 0.80,
    "answer_relevancy": 0.70,
}

REFUSAL_KEYWORDS = [
    "brak informacji",
    "nie wiem",
    "nie zawiera",
    "brak danych",
    "nie wynika",
    "nie wiesz",
]

SYSTEM_PROMPT_TEMPLATE = (
    "Odpowiedz na pytanie na podstawie podanego kontekstu. "
    "Możesz łączyć i wnioskować z powiązanych fragmentów kontekstu. "
    "Tylko jeśli w kontekście zupełnie brak jakichkolwiek informacji na ten temat, "
    "napisz: 'Brak informacji w podanym kontekście.'\n\n"
    "Kontekst:\n{context}\n\nPytanie: {question}"
)
