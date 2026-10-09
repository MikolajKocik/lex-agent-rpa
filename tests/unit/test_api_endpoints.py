import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routers.agent import _TASK_STORE
from src.api.routers.agent import router as agent_router


@pytest.fixture
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(agent_router, prefix="/api")
    return app


def test_healthcheck_endpoint(test_app: FastAPI) -> None:
    client = TestClient(test_app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}



def test_get_task_status_not_found(test_app: FastAPI) -> None:
    client = TestClient(test_app)
    response = client.get("/api/task/non-existent-uuid-12345")
    assert response.status_code == 404


def test_get_task_status_completed(test_app: FastAPI) -> None:
    client = TestClient(test_app)
    task_id = "test-task-123"
    _TASK_STORE[task_id] = {
        "status": "completed",
        "result": "Analiza umowy pomyślna.",
        "error": None,
    }

    response = client.get(f"/api/task/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "completed"
    assert data["result"] == "Analiza umowy pomyślna."
