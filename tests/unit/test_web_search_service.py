from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.infrastructure.services.web_search_service import TavilySearchService


@pytest.fixture
def mock_httpx_client():
    client = MagicMock(spec=httpx.AsyncClient)
    client.post = AsyncMock()
    return client

@pytest.mark.asyncio
async def test_search_private_method_returns_parsed_results(mock_httpx_client):
    service = TavilySearchService(client=mock_httpx_client, max_results=2, api_key="dummy_key")
    
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "title": "Python - A programming language",
                "content": "Python is an interpreted, high-level, general-purpose programming language.",
                "url": "https://python.org"
            },
            {
                "title": "Pytest - A testing framework",
                "content": "The pytest framework makes it easy to write small tests.",
                "url": "https://pytest.org"
            }
        ]
    }
    mock_httpx_client.post.return_value = mock_response

    results = await service._search("pytest")

    mock_httpx_client.post.assert_called_once()
    assert len(results) == 2
    
    assert results[0]["title"] == "Python - A programming language"
    assert results[0]["url"] == "https://python.org"
    assert results[0]["snippet"] == "Python is an interpreted, high-level, general-purpose programming language."
    
    assert results[1]["title"] == "Pytest - A testing framework"
    assert results[1]["url"] == "https://pytest.org"
    assert results[1]["snippet"] == "The pytest framework makes it easy to write small tests."

def test_format_results_private_method():
    service = TavilySearchService(client=MagicMock(), api_key="dummy")
    raw_results = [
        {"title": "Test Title", "snippet": "Test Snippet", "url": "https://test.com"}
    ]
    
    formatted = service._format_results(raw_results)
    
    assert "Result [1]:" in formatted
    assert "Title: Test Title" in formatted
    assert "Snippet: Test Snippet" in formatted
    assert "URL: https://test.com" in formatted
