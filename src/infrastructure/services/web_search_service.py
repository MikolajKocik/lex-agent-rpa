import httpx
from src.core.decorators import http_retry, log_execution
from typing import Protocol

class WebService(Protocol):
    async def __call__(self, query: str) -> str: ...

class DuckDuckGoService:
    def __init__(self, client: httpx.AsyncClient, max_results=5) -> None:
        self.client = client
        self.max_results = max_results

    def __str__(self):
        return "GraphService(AI Agent Engine)"
    
    def __repr__(self):
        """
        Defines which rail object a service has right now 
        """
        return f"GraphService(rails={self.rails.__class__.__name__})"

    @log_execution()
    @http_retry
    async def _search(self, query: str) -> list[dict]:
        """
        Web search using DuckDuckGo browser with no tracking and block ads
        """
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }

        response = await self.client.get(
            "https://api.duckduckgo.com/",
            params=params
        )
        response.raise_for_status()

        data = response.json()
        raw_topics = data.get("RelatedTopics", [])

        results: list[dict] = []
        for item in raw_topics:
            if "Topics" in item:
                for sub_item in item["Topics"]:
                    results.append({
                        "title": sub_item.get("Text", "").split(" - ")[0],
                        "snippet": sub_item.get("Text", ""),
                        "url": sub_item.get("FirstURL", ""),
                    })
            elif "Text" in item:
                results.append({
                    "title": item.get("Text", "").split(" - ")[0],
                    "snippet": item.get("Text", ""),
                    "url": item.get("FirstURL", ""),
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
            snippet = item.get("body", item.get("snippet", ""))
            url = item.get("href", item.get("link", ""))

            # use literal concatenation for concatenate strings
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
