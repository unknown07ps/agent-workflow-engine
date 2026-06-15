"""Tests for app.core.runner.run_workflow."""

from __future__ import annotations

import json

from app.core.runner import run_workflow
from app.core.store import TaskStore
from app.models.schemas import TaskStatus


def test_run_workflow_success(fake_redis, mock_llm):
    store = TaskStore(client=fake_redis)
    record = run_workflow("task-1", "Write a report on X", max_revisions=2, store=store)

    assert record.status == TaskStatus.COMPLETED
    assert record.final_report == "# Report\n\nContent here."
    assert record.error is None
    assert record.revision_count == 0
    assert len(record.trace) == 4

    persisted = store.get("task-1")
    assert persisted.status == TaskStatus.COMPLETED
    assert persisted.final_report == record.final_report


def test_run_workflow_with_revision(fake_redis, mock_llm, llm_responses):
    llm_responses["critic"] = [
        json.dumps({"approved": False, "feedback": "Add more detail"}),
        json.dumps({"approved": True, "feedback": "Looks good now"}),
    ]

    store = TaskStore(client=fake_redis)
    record = run_workflow("task-1", "Write a report on X", max_revisions=2, store=store)

    assert record.status == TaskStatus.COMPLETED
    assert record.revision_count == 1
    assert len(record.trace) == 7


def test_run_workflow_failure(fake_redis, mock_llm, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr("app.agents.planner.call_llm", boom)

    store = TaskStore(client=fake_redis)
    record = run_workflow("task-1", "Write a report on X", max_revisions=2, store=store)

    assert record.status == TaskStatus.FAILED
    assert record.error == "LLM unavailable"
    assert record.final_report is None

    persisted = store.get("task-1")
    assert persisted.status == TaskStatus.FAILED


def test_run_workflow_creates_record_if_missing(fake_redis, mock_llm):
    store = TaskStore(client=fake_redis)
    assert store.get("new-task") is None

    record = run_workflow("new-task", "Write a report on X", max_revisions=2, store=store)

    assert record.task_id == "new-task"
    assert record.status == TaskStatus.COMPLETED
    assert store.get("new-task") is not None
