import httpx
from src.core.decorators import http_retry, log_execution
from typing import Protocol
from src.infrastructure.keyvault.client import TAVILY_API_KEY

class WebService(Protocol):
    async def __call__(self, query: str) -> str: ...

class TavilySearchService:
    def __init__(self, client: httpx.AsyncClient, max_results=5, api_key: str = None) -> None:
        self.client = client
        self.max_results = max_results
        self.api_key = api_key or TAVILY_API_KEY
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY from KeyVault is missing.")

    def __str__(self):
        return "TavilySearchService(AI Agent Web Search Engine)"
    
    def __repr__(self):
        return f"TavilySearchService(rails={self.rails.__class__.__name__})" if hasattr(self, "rails") else "TavilySearchService()"

    @log_execution()
    @http_retry
    async def _search(self, query: str) -> list[dict]:
        """
        Web search using Tavily API, specifically built for LLMs and Agents.
        """
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": self.max_results
        }

        response = await self.client.post(
            "https://api.tavily.com/search",
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        raw_results = data.get("results", [])

        results: list[dict] = []
        for item in raw_results:
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("content", ""), 
                "url": item.get("url", ""),
            })
            
            if len(results) >= self.max_results:
                break
        
        return results

    def _format_results(self, raw_results: list[dict]) -> str:
        """
        A helper method that converts a list of dictionaries into plain text for the prompt
        """
        if not raw_results:
            return "No results found."

        formatted_items: list[str] = []

        for idx, item in enumerate(raw_results, start=1):
            title = item.get("title", "No Title")
            snippet = item.get("snippet", "")
            url = item.get("url", "")

            entry = (
                f"Result [{idx}]:\n"
                f"Title: {title}\n"
                f"Snippet: {snippet}\n"
                f"URL: {url}"
            )
            formatted_items.append(entry)

        return "\n\n".join(formatted_items)

    async def __call__(self, query: str) -> str:
        result = await self._search(query)
        return self._format_results(result)
