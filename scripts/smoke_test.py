"""Manual smoke test: starts the FastAPI app with mocked LLM calls and exercises
the full /tasks lifecycle via TestClient. Not part of the pytest suite (Stage 6
adds proper tests) - this is a quick end-to-end sanity check.

Run with: python3 scripts/smoke_test.py
"""

from __future__ import annotations

import json
import time
import unittest.mock as mock

responses = {
    "planner": "1. Sub-topic A\n2. Sub-topic B",
    "researcher": "Research findings about A and B.",
    "formatter": "# Report\n\nContent here.",
    "critic_approve": json.dumps({"approved": True, "feedback": "Looks good"}),
}


def fake_call_llm(system_prompt, user_prompt, temperature=0.3):
    if "Planner" in system_prompt:
        return responses["planner"]
    if "Researcher" in system_prompt:
        return responses["researcher"]
    if "Formatter" in system_prompt:
        return responses["formatter"]
    if "Critic" in system_prompt:
        return responses["critic_approve"]
    return "unknown"


def main():
    with mock.patch("app.agents.planner.call_llm", side_effect=fake_call_llm), \
         mock.patch("app.agents.researcher.call_llm", side_effect=fake_call_llm), \
         mock.patch("app.agents.formatter.call_llm", side_effect=fake_call_llm), \
         mock.patch("app.agents.critic.call_llm", side_effect=fake_call_llm):

        from fastapi.testclient import TestClient
        from app.api.main import app

        client = TestClient(app)

        print("== /health ==")
        print(client.get("/health").json())

        print("\n== POST /tasks ==")
        resp = client.post("/tasks", json={"task": "Write a report on renewable energy", "max_revisions": 1})
        print(resp.status_code, resp.json())
        task_id = resp.json()["task_id"]

        # BackgroundTasks run synchronously within the TestClient request in
        # newer Starlette versions, but poll briefly just in case.
        for _ in range(20):
            record = client.get(f"/tasks/{task_id}").json()
            if record["status"] in ("completed", "failed"):
                break
            time.sleep(0.2)

        print("\n== GET /tasks/{id} ==")
        print(json.dumps(record, indent=2, default=str)[:1500])

        print("\n== GET /tasks/{id}/trace ==")
        trace = client.get(f"/tasks/{task_id}/trace").json()
        for t in trace["trace"]:
            print(f"- {t['agent']} approved={t['metadata'].get('approved')} rev={t['metadata'].get('revision_count')}")

        print("\n== GET /tasks/{id}/result ==")
        print(client.get(f"/tasks/{task_id}/result").json())

        print("\n== GET /tasks (list) ==")
        print(client.get("/tasks").json())

        print("\n== DELETE /tasks/{id} ==")
        print(client.delete(f"/tasks/{task_id}").json())

        print("\n== GET /tasks/{id} after delete (expect 404) ==")
        resp = client.get(f"/tasks/{task_id}")
        print(resp.status_code, resp.json())


if __name__ == "__main__":
    main()
