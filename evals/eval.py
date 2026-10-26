"""
Ewaluacja RAG z osobnym raportowaniem retrievalu, generacji oraz testu odmowy.

Uzycie:
    python -m evals.eval [opcje]
    python -m evals.eval --ci --output-dir evals/reports
"""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import warnings

from dotenv import load_dotenv
import pandas as pd

load_dotenv()
if "GOOGLE_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
os.environ.setdefault("USER_AGENT", "LexAgentRPA/1.0")

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_google_genai")

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


def write_summary_md(
    path: Path,
    run_name: str,
    config: dict,
    summary: dict,
    failures: list[dict],
    unanswerable_df: pd.DataFrame = None,
) -> None:
    """Zapisuje podsumowanie ewaluacji w formacie Markdown (kompatybilne z GitHub Step Summary)."""
    all_passed = all(s["passed"] for s in summary.values())
    status_text = "SUKCES" if all_passed else "NIEPOWODZENIE"

    lines = [
        f"# Raport Ewaluacji RAG: {run_name}",
        "",
        f"- Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Status: [{status_text}]",
        "",
        "## Podsumowanie Metryk",
        "",
        "| Metryka | Etap | Srednia | Prog | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for m, s in summary.items():
        status = "PASS" if s["passed"] else "FAIL"
        lines.append(f"| `{m}` | {s['stage']} | **{s['mean']:.2f}** | {s['threshold']:.2f} | {status} |")

    if failures:
        lines.extend([
            "",
            "## Pytania Ponizej Progu",
            "",
            "| Metryka | Pytanie | Wynik |",
            "| :--- | :--- | :--- |",
        ])
        for f in failures:
            lines.append(f"| `{f['metric']}` | {f['question']} | {f['score']:.2f} |")

    if unanswerable_df is not None and not unanswerable_df.empty:
        lines.extend([
            "",
            "## Test Odmowy",
            "",
            "| Pytanie | Status | Odpowiedz |",
            "| :--- | :--- | :--- |",
        ])
        for _, row in unanswerable_df.iterrows():
            resp = str(row["response"]).replace("\n", " ").strip()
            if len(resp) > 100:
                resp = resp[:97] + "..."
            lines.append(f"| {row['user_input']} | {row['status']} | {resp} |")

    lines.extend([
        "",
        "## Konfiguracja",
        "",
        "| Parametr | Wartosc |",
        "| :--- | :--- |",
    ])
    for k, v in config.items():
        lines.append(f"| `{k}` | `{v}` |")

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Ewaluacja potoku RAG za pomoca metryk Ragas")
    parser.add_argument("--name", type=str, default=None, help="Nazwa przebiegu ewaluacji")
    parser.add_argument("--k", type=int, default=RAG_CONFIG["top_k"], help="Liczba dokumentow w retrieval (top_k)")
    parser.add_argument("--chunk-size", type=int, default=RAG_CONFIG["chunk_size"], help="Rozmiar chunka")
    parser.add_argument("--chunk-overlap", type=int, default=RAG_CONFIG["chunk_overlap"], help="Nakladanie chunkow")
    parser.add_argument("--cases", type=Path, default=TEST_CASES_PATH, help="Sciezka do pliku test_cases.json")
    parser.add_argument("--unanswerable", type=Path, default=UNANSWERABLE_PATH, help="Sciezka do pliku unanswerable.json")
    parser.add_argument("--output-dir", type=Path, default=REPORTS_DIR, help="Katalog zapisu raportow")
    parser.add_argument("--ci", action="store_true", help="Tryb CI: zapisuje summary.md dla GitHub Step Summary")
    args = parser.parse_args()

    effective_config = {**RAG_CONFIG, "top_k": args.k, "chunk_size": args.chunk_size, "chunk_overlap": args.chunk_overlap}
    base_name = args.name or datetime.now().strftime("%Y%m%d-%H%M%S")
    run_name = f"{base_name}_k{effective_config['top_k']}_c{effective_config['chunk_size']}"

    print(f"=== Uruchamianie ewaluacji: {run_name} ===")
    answerable_cases = load_dataset(args.cases)
    unanswerable_cases = load_dataset(args.unanswerable) if args.unanswerable.exists() else []

    print("Budowanie wektorow FAISS...")
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
            ResponseRelevancy(llm=judge, embeddings=judge_emb, name="answer_relevancy", strictness=1),
        ],
        run_config=run_config,
    ).to_pandas()

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

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_md_path = args.output_dir / "summary.md"
    write_summary_md(summary_md_path, run_name, effective_config, summary, failures, unanswerable_df)
    print(f"\n[OK] Zapisano podsumowanie Markdown: {summary_md_path}")

    print("\n--- WYNIKI ---")
    for m, s in summary.items():
        status = "PASS" if s["passed"] else "FAIL"
        print(f"[{status}] {m} ({s['stage']}): {s['mean']:.2f} (prog: {s['threshold']:.2f})")

    failed = [m for m, s in summary.items() if not s["passed"]]
    if failed:
        stages = sorted({summary[m]["stage"] for m in failed})
        print(f"\n[BLAD] Metryki ponizej progu: {', '.join(failed)}")
        print(f"Etapy do weryfikacji: {', '.join(stages)}")
        sys.exit(1)

    print("\n[SUKCES] Wszystkie metryki powyzej progow jakosciowych!")


if __name__ == "__main__":
    main()