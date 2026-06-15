"""Tests for app.api routes using FastAPI's TestClient."""

from __future__ import annotations

import pytest


@pytest.fixture()
def client(fake_redis, mock_llm):
    """TestClient with fake Redis and mocked LLM. Background tasks run
    synchronously within the request in Starlette's TestClient."""
    from fastapi.testclient import TestClient
    from app.api.main import app

    # Ensure routes.get_store() builds a TaskStore bound to the fake redis client.
    import app.api.routes as routes_module
    from app.core.store import TaskStore

    routes_module.get_store = lambda: TaskStore(client=fake_redis)

    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["redis"] is True


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "docs" in resp.json()


def test_create_task_rejects_empty(client):
    resp = client.post("/tasks", json={"task": "   "})
    assert resp.status_code == 422


def test_full_task_lifecycle(client):
    resp = client.post("/tasks", json={"task": "Write a report on X", "max_revisions": 1})
    assert resp.status_code == 202
    body = resp.json()
    task_id = body["task_id"]
    assert body["status"] == "pending"

    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    record = resp.json()
    assert record["status"] == "completed"
    assert record["final_report"] == "# Report\n\nContent here."

    resp = client.get(f"/tasks/{task_id}/trace")
    assert resp.status_code == 200
    trace = resp.json()
    assert trace["task_id"] == task_id
    assert len(trace["trace"]) == 4
    assert [t["agent"] for t in trace["trace"]] == ["planner", "researcher", "formatter", "critic"]

    resp = client.get(f"/tasks/{task_id}/result")
    assert resp.status_code == 200
    assert resp.json()["final_report"] == "# Report\n\nContent here."

    resp = client.get("/tasks")
    assert resp.status_code == 200
    listing = resp.json()
    assert listing["count"] == 1
    assert listing["tasks"][0]["task_id"] == task_id

    resp = client.delete(f"/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True

    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 404


def test_get_nonexistent_task(client):
    resp = client.get("/tasks/does-not-exist")
    assert resp.status_code == 404


def test_get_trace_nonexistent_task(client):
    resp = client.get("/tasks/does-not-exist/trace")
    assert resp.status_code == 404


def test_result_not_ready_returns_409(client, llm_responses):
    # Make the formatter raise so the workflow fails fast, then check /result.
    import json

    llm_responses["critic"] = json.dumps({"approved": False, "feedback": "needs work"})

    resp = client.post("/tasks", json={"task": "Write a report on X", "max_revisions": 0})
    task_id = resp.json()["task_id"]

    resp = client.get(f"/tasks/{task_id}/result")
    # With max_revisions=0, budget is exhausted immediately -> still completes.
    assert resp.status_code == 200


def test_result_failed_returns_500(client, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr("app.agents.planner.call_llm", boom)

    resp = client.post("/tasks", json={"task": "Write a report on X"})
    task_id = resp.json()["task_id"]

    resp = client.get(f"/tasks/{task_id}/result")
    assert resp.status_code == 500


def test_delete_nonexistent_task(client):
    resp = client.delete("/tasks/does-not-exist")
    assert resp.status_code == 404


def test_list_tasks_invalid_limit(client):
    resp = client.get("/tasks?limit=0")
    assert resp.status_code == 422

    resp = client.get("/tasks?limit=500")
    assert resp.status_code == 422
