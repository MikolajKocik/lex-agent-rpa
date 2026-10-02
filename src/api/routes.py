from fastapi import APIRouter
from .schemas import AgentTaskRequest, AgentTaskResponse

router = APIRouter(tags=["Agent"])

@router.post("/task", response_model=AgentTaskResponse)
async def execute_agent_task(request: AgentTaskRequest):
    """
    Główny punkt wejścia dla agenta. Przyjmuje cel/zadanie (np. "Przeanalizuj umowę X i przenieś do archiwum Y").
    Agent w tle decyduje, jakich Narzędzi (Tools) użyć do wykonania zadania.
    """
    
    # TODO
    pass

@router.get("/health")
def healthcheck():
    return { "status": "ok" }
