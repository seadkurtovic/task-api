from fastapi.testclient import TestClient

import app.main as task_api


client = TestClient(task_api.app)


def setup_function() -> None:
    task_api._tasks.clear()
    task_api._next_id = 1


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_tasks() -> None:
    create_response = client.post("/tasks", json={"title": "Learn CI/CD"})

    assert create_response.status_code == 200
    assert create_response.json() == {"id": 1, "title": "Learn CI/CD", "done": False}

    list_response = client.get("/tasks")

    assert list_response.status_code == 200
    assert list_response.json() == {"tasks": [{"id": 1, "title": "Learn CI/CD", "done": False}]}
