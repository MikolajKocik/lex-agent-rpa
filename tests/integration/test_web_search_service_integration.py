import os

import httpx
import pytest

from src.infrastructure.services.web_search_service import TavilySearchService


@pytest.mark.asyncio
async def test_live_search_tavily_returns_valid_results():
    """
    Integration test. Executes a real network request to the Tavily API.
    Proves that the external dependency is working as expected.
    This test skips if TAVILY_API_KEY is missing or is a mock placeholder.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or api_key in ("mock_tavily_key", "dummy_key") or api_key.startswith("mock_"):
        pytest.skip("Valid TAVILY_API_KEY is required to run live Tavily integration test.")

    async with httpx.AsyncClient(timeout=10.0) as client:
        service = TavilySearchService(client=client, max_results=3, api_key=api_key)

        results = await service._search("Python")

        assert len(results) > 0, "Expected search results from the internet"
        assert len(results) <= 3, "Results should not exceed the max_results limit"

        for item in results:
            assert "title" in item
            assert "snippet" in item
            assert "url" in item

            assert item["url"].startswith("http"), f"Received malformed URL: {item['url']}"
