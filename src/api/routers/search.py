from src.infrastructure.services.web_search_service import WebService
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api.dependencies import get_web_search_service

router = APIRouter(prefix="/search", tags=["Search"])

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    results: str

@router.post("/", response_model=SearchResponse)
async def execute_web_search(
    payload: SearchRequest,
    search_service: WebService = Depends(get_web_search_service)
):
    text_results = await search_service(payload.query)
    return SearchResponse(results=text_results)