import json
from pathlib import Path
from src.rag.models import SearchResultChunk


def compute_hit_rate_at_k(
    ranked_results: list[list[SearchResultChunk]],
    expected_articles: list[str],
    k: int = 3,
) -> float:
    """Computes Hit-Rate@K metric indicating whether the correct article was retrieved in the top K."""
    hits = 0
    total = len(expected_articles)

    for results, expected in zip(ranked_results, expected_articles):
        top_k_chunks = results[:k]
        matched = any(expected.lower() in (chunk.article_number or "").lower() for chunk in top_k_chunks)
        if matched:
            hits += 1

    return hits / total if total > 0 else 0.0


def compute_mean_reciprocal_rank(
    ranked_results: list[list[SearchResultChunk]],
    expected_articles: list[str],
) -> float:
    """Computes Mean Reciprocal Rank (MRR) evaluating ranking quality of relevant items."""
    reciprocal_ranks: list[float] = []

    for results, expected in zip(ranked_results, expected_articles):
        found_rank = 0
        for rank, chunk in enumerate(results, start=1):
            if expected.lower() in (chunk.article_number or "").lower():
                found_rank = rank
                break

        if found_rank > 0:
            reciprocal_ranks.append(1.0 / found_rank)
        else:
            reciprocal_ranks.append(0.0)

    return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0


def test_eval_dataset_schema_and_size() -> None:
    dataset_path = Path(__file__).parent / "eval_dataset.json"
    assert dataset_path.exists()

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) >= 10
    for item in data:
        assert "id" in item
        assert "query" in item
        assert "expected_article" in item
        assert "ground_truth_snippet" in item


def test_hit_rate_and_mrr_calculations() -> None:
    mock_ranked_results = [
        [
            SearchResultChunk(
                chunk_id="1",
                article_number="Art. 167",
                paragraph=None,
                content="Urlop na żądanie",
                score=0.98,
            ),
            SearchResultChunk(
                chunk_id="2",
                article_number="Art. 150",
                paragraph=None,
                content="Czas pracy",
                score=0.85,
            ),
        ],
        [
            SearchResultChunk(
                chunk_id="3",
                article_number="Art. 100",
                paragraph=None,
                content="Obowiązki",
                score=0.90,
            ),
            SearchResultChunk(
                chunk_id="4",
                article_number="Art. 52",
                paragraph=None,
                content="Dyscyplinarka",
                score=0.88,
            ),
        ],
    ]

    expected = ["Art. 167", "Art. 52"]

    hit_rate_1 = compute_hit_rate_at_k(mock_ranked_results, expected, k=1)
    hit_rate_2 = compute_hit_rate_at_k(mock_ranked_results, expected, k=2)
    mrr = compute_mean_reciprocal_rank(mock_ranked_results, expected)

    assert hit_rate_1 == 0.5
    assert hit_rate_2 == 1.0
    assert mrr == (1.0 / 1 + 1.0 / 2) / 2
