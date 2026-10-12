"""
Ewaluacja RAG z osobnym raportowaniem retrievalu, generacji oraz testu odmowy.

Użycie:
    python -m evals.eval [opcje]
    python evals/eval.py [opcje]

Przykłady:
    python -m evals.eval
    python -m evals.eval --name eksperyment_v2
    python -m evals.eval --k 5 --chunk-size 1000
"""

import argparse
from datetime import datetime
from html import escape
import json
import os
from pathlib import Path
import sys
import warnings

from dotenv import load_dotenv
import numpy as np
import pandas as pd

load_dotenv()
if "GOOGLE_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
os.environ.setdefault("USER_AGENT", "LexAgentRPA/1.0")

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_google_genai")

try:
    from evals.config import (
        GENERATION_THRESHOLDS,
        RAG_CONFIG,
        REFUSAL_KEYWORDS,
        REPORTS_DIR,
        RETRIEVAL_THRESHOLDS,
        SYSTEM_PROMPT_TEMPLATE,
        TEST_CASES_PATH,
        UNANSWERABLE_PATH,
        URLS,
    )
except ImportError:
    from evals.config import (
        GENERATION_THRESHOLDS,
        RAG_CONFIG,
        REFUSAL_KEYWORDS,
        REPORTS_DIR,
        RETRIEVAL_THRESHOLDS,
        SYSTEM_PROMPT_TEMPLATE,
        TEST_CASES_PATH,
        UNANSWERABLE_PATH,
        URLS,
    )

from src.core.config.llm_provider import GoogleLLMProvider

from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
    ResponseRelevancy,
)
from ragas.run_config import RunConfig


def load_dataset(file_path: Path) -> list[dict]:
    """Wczytuje zbiór pytań testowych z pliku JSON."""
    if not file_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku z danymi testowymi: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_vectorstore(urls: list[str], chunk_size: int, chunk_overlap: int, embedding_model: str):
    """Pobiera dokumenty źródłowe i buduje indeks wektorowy FAISS."""
    loader = WebBaseLoader(
        urls,
        header_template={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        },
    )
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    splits = splitter.split_documents(docs)

    emb = GoogleGenerativeAIEmbeddings(model=embedding_model)
    vectorstore = FAISS.from_documents(documents=splits, embedding=emb)
    return vectorstore, emb


def run_rag(question: str, retriever, answer_chain) -> dict:
    """Wykonuje pojedyncze zapytanie RAG: pobiera konteksty i generuje odpowiedź."""
    docs = retriever.invoke(question)
    context = "\n\n".join(d.page_content for d in docs)
    response = answer_chain.invoke({"context": context, "question": question})
    return {
        "response": response,
        "contexts": [d.page_content for d in docs],
    }


def build_samples(cases: list[dict], retriever, answer_chain) -> list[SingleTurnSample]:
    """Generuje próbki SingleTurnSample dla zadanego zbioru przypadków testowych."""
    samples = []
    for case in cases:
        out = run_rag(case["question"], retriever, answer_chain)
        samples.append(
            SingleTurnSample(
                user_input=case["question"],
                retrieved_contexts=out["contexts"],
                response=out["response"],
                reference=case.get("reference"),
            )
        )
    return samples


def check_refusal(samples: list[SingleTurnSample], refusal_keywords: list[str]) -> pd.DataFrame:
    """Sprawdza czy model poprawnie odmówił odpowiedzi na pytania spoza źródeł."""
    rows = []
    for s in samples:
        resp_lower = s.response.lower()
        refused = any(kw in resp_lower for kw in refusal_keywords)
        rows.append({
            "user_input": s.user_input,
            "response": s.response,
            "status": "OK (Poprawna odmowa)" if refused else "FAIL (Halucynacja)",
        })
    return pd.DataFrame(rows)


def row_failures(df: pd.DataFrame, thresholds: dict) -> list[dict]:
    """Identyfikuje wiersze, w których wynik metryki spadł poniżej progu."""
    failures = []
    for metric, limit in thresholds.items():
        if metric in df.columns:
            for _, row in df[df[metric] < limit].iterrows():
                failures.append({
                    "metric": metric,
                    "question": row["user_input"],
                    "score": float(row[metric]),
                })
    return failures


def _color_scale(val):
    """Zwraca styl koloru w formacie HSL dla wartości od 0.0 do 1.0 (bez zależności od matplotlib)."""
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return "background-color: #f0f0f0; color: #888;"
        score = max(0.0, min(1.0, float(val)))
        hue = int(score * 120)
        return f"background-color: hsl({hue}, 70%, 85%); color: #111;"
    except (ValueError, TypeError):
        return ""


def style_table(df: pd.DataFrame, metrics: list[str], caption: str, include_response: bool = False) -> str:
    """Generuje ostylowaną tabelę HTML ze wskaźnikami jakości."""
    cols = ["user_input"]
    if include_response and "response" in df.columns:
        cols.append("response")
    cols.extend(metrics)
    return (
        df[cols]
        .style
        .map(_color_scale, subset=metrics)
        .format("{:.2f}", subset=metrics, na_rep="N/A")
        .set_caption(caption)
        .hide(axis="index")
        .to_html()
    )


def style_unanswerable_table(df: pd.DataFrame, caption: str = "Pytania bez odpowiedzi w źródłach (Test odmowy)") -> str:
    """Generuje tabelę HTML dla testu odmowy."""
    def _status_color(val):
        return "background-color: #d4edda; color: #155724;" if "OK" in str(val) else "background-color: #f8d7da; color: #721c24;"

    return (
        df.style
        .map(_status_color, subset=["status"])
        .set_caption(caption)
        .hide(axis="index")
        .to_html()
    )


def write_report(
    path: Path,
    run_name: str,
    config: dict,
    summary: dict,
    failures: list[dict],
    retrieval_df: pd.DataFrame,
    generation_df: pd.DataFrame,
    unanswerable_df: pd.DataFrame = None,
) -> None:
    """Zapisuje kompletny raport ewaluacyjny do pliku HTML."""
    summary_rows = "".join(
        f"<tr><td>{m}</td><td>{s['stage']}</td><td>{s['mean']:.2f}</td>"
        f"<td>{s['threshold']:.2f}</td><td>{'OK' if s['passed'] else 'FAIL'}</td></tr>"
        for m, s in summary.items()
    )
    failure_rows = "".join(
        f"<tr><td>{f['metric']}</td><td>{escape(f['question'])}</td><td>{f['score']:.2f}</td></tr>"
        for f in failures
    ) or "<tr><td colspan='3'>Brak</td></tr>"
    config_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in config.items())

    unanswerable_section = ""
    if unanswerable_df is not None and not unanswerable_df.empty:
        unanswerable_section = f"<h2>Pytania bez odpowiedzi (Test odmowy)</h2>{style_unanswerable_table(unanswerable_df)}"

    html = f"""<!DOCTYPE html>
        <html><head><meta charset="utf-8"><title>{escape(run_name)}</title>
        <style>
        body {{ font-family: sans-serif; margin: 2em; }}
        table {{ border-collapse: collapse; margin-bottom: 2em; }}
        td, th {{ border: 1px solid #ccc; padding: 4px 8px; text-align: left; }}
        </style></head><body>
        <h1>Raport ewaluacji RAG</h1>
        <p>Przebieg: <b>{escape(run_name)}</b></p>
        <h2>Konfiguracja</h2>
        <table>{config_rows}</table>
        <h2>Podsumowanie</h2>
        <table><tr><th>Metryka</th><th>Etap</th><th>Średnia</th><th>Próg</th><th>Wynik</th></tr>{summary_rows}</table>
        <h2>Pytania poniżej progu (per wiersz)</h2>
        <table><tr><th>Metryka</th><th>Pytanie</th><th>Wynik</th></tr>{failure_rows}</table>
        <h2>Retrieval</h2>
        {style_table(retrieval_df, list(RETRIEVAL_THRESHOLDS), "Retrieval")}
        <h2>Generacja (Pytania ze źródeł)</h2>
        {style_table(generation_df, list(GENERATION_THRESHOLDS), "Generacja", include_response=True)}
        {unanswerable_section}
        </body></html>
    """
    path.write_text(html, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Ewaluacja potoku RAG za pomocą metryk Ragas")
    parser.add_argument("--name", type=str, default=None, help="Nazwa przebiegu ewaluacji")
    parser.add_argument("--k", type=int, default=RAG_CONFIG["top_k"], help="Liczba dokumentów w retrieval (top_k)")
    parser.add_argument("--chunk-size", type=int, default=RAG_CONFIG["chunk_size"], help="Rozmiar chunka")
    parser.add_argument("--chunk-overlap", type=int, default=RAG_CONFIG["chunk_overlap"], help="Nakładanie chunków")
    parser.add_argument("--cases", type=Path, default=TEST_CASES_PATH, help="Ścieżka do pliku test_cases.json")
    parser.add_argument("--unanswerable", type=Path, default=UNANSWERABLE_PATH, help="Ścieżka do pliku unanswerable.json")
    args = parser.parse_args()

    effective_config = dict(RAG_CONFIG)
    effective_config["top_k"] = args.k
    effective_config["chunk_size"] = args.chunk_size
    effective_config["chunk_overlap"] = args.chunk_overlap

    base_name = args.name or datetime.now().strftime("%Y%m%d-%H%M%S")
    run_name = f"{base_name}_k{effective_config['top_k']}_c{effective_config['chunk_size']}"

    print(f"=== Uruchamianie ewaluacji: {run_name} ===")
    print(f"Ładowanie przypadków testowych z: {args.cases}")
    answerable_cases = load_dataset(args.cases)
    unanswerable_cases = load_dataset(args.unanswerable) if args.unanswerable.exists() else []

    print("Ładowanie dokumentów źródłowych i budowanie wektorów...")
    vectorstore, emb = build_vectorstore(
        urls=URLS,
        chunk_size=effective_config["chunk_size"],
        chunk_overlap=effective_config["chunk_overlap"],
        embedding_model=effective_config["embedding_model"],
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": effective_config["top_k"]})

    llm = GoogleLLMProvider(temperature=effective_config["generator_temperature"]).model
    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT_TEMPLATE)
    answer_chain = prompt | llm | StrOutputParser()

    print("Generowanie odpowiedzi RAG na pytania testowe...")
    answerable_samples = build_samples(answerable_cases, retriever, answer_chain)
    unanswerable_samples = build_samples(unanswerable_cases, retriever, answer_chain)

    print("Uruchamianie ewaluacji Ragas...")
    judge = LangchainLLMWrapper(llm)
    judge_emb = LangchainEmbeddingsWrapper(emb)
    run_config = RunConfig(timeout=300, max_workers=1, max_retries=10)

    print("- Ocenianie etapu Retrieval...")
    retrieval_df = evaluate(
        dataset=EvaluationDataset(samples=answerable_samples),
        metrics=[
            LLMContextPrecisionWithReference(llm=judge, name="context_precision_with_reference"),
            LLMContextRecall(llm=judge, name="context_recall"),
        ],
        run_config=run_config,
    ).to_pandas()

    print("- Ocenianie etapu Generacji...")
    generation_df = evaluate(
        dataset=EvaluationDataset(samples=answerable_samples),
        metrics=[
            Faithfulness(llm=judge, name="faithfulness"),
            ResponseRelevancy(
                llm=judge,
                embeddings=judge_emb,
                name="answer_relevancy",
                strictness=1,
            ),
        ],
        run_config=run_config,
    ).to_pandas()

    # Weryfikacja odmowy
    unanswerable_df = check_refusal(unanswerable_samples, REFUSAL_KEYWORDS)

    summary = {}
    for stage, df, thresholds in [
        ("retrieval", retrieval_df, RETRIEVAL_THRESHOLDS),
        ("generation", generation_df, GENERATION_THRESHOLDS),
    ]:
        for metric, limit in thresholds.items():
            mean = float(df[metric].mean())
            summary[metric] = {
                "stage": stage,
                "mean": mean,
                "threshold": limit,
                "passed": mean >= limit,
            }

    failures = row_failures(retrieval_df, RETRIEVAL_THRESHOLDS) + row_failures(
        generation_df, GENERATION_THRESHOLDS
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{run_name}.html"
    write_report(
        report_path, run_name, effective_config, summary, failures, retrieval_df, generation_df, unanswerable_df
    )
    print(f"\n[OK] Zapisano raport: {report_path}")

    failed = [m for m, s in summary.items() if not s["passed"]]
    if failed:
        stages = sorted({summary[m]["stage"] for m in failed})
        print(f"[UWAGA] Metryki poniżej progu: {', '.join(failed)}")
        print(f"Etapy do weryfikacji: {', '.join(stages)}")
        sys.exit(1)

    print("[SUKCES] Wszystkie metryki powyżej progów jakościowych!")


if __name__ == "__main__":
    main()