from langchain_core.tools import tool
import httpx

SEARCH_API_URL = "http://localhost:8000/search/"

@tool 
async def web_search_tool(query: str) -> str: 
    """Search the web for current information, technical documentation, or facts."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(SEARCH_API_URL, json={"query": query})
        response.raise_for_status()
        data = response.json()
        return data["results"]