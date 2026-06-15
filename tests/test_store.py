"""Tests for app.core.store.TaskStore using fakeredis."""

from __future__ import annotations

from app.core.store import TaskStore
from app.models.schemas import AgentName, TaskRecord, TaskStatus, TraceEntry


def test_save_and_get(fake_redis):
    store = TaskStore(client=fake_redis)
    record = TaskRecord(task="Do the thing", max_revisions=2)
    store.save(record)

    fetched = store.get(record.task_id)
    assert fetched is not None
    assert fetched.task_id == record.task_id
    assert fetched.task == "Do the thing"
    assert fetched.status == TaskStatus.PENDING


def test_get_missing_returns_none(fake_redis):
    store = TaskStore(client=fake_redis)
    assert store.get("does-not-exist") is None


def test_exists(fake_redis):
    store = TaskStore(client=fake_redis)
    record = TaskRecord(task="Do the thing")
    store.save(record)

    assert store.exists(record.task_id) is True
    assert store.exists("nope") is False


def test_list_recent_ordering(fake_redis):
    store = TaskStore(client=fake_redis)

    r1 = TaskRecord(task="first", created_at=1.0)
    r2 = TaskRecord(task="second", created_at=2.0)
    r3 = TaskRecord(task="third", created_at=3.0)

    for r in (r1, r2, r3):
        store.save(r)

    recent = store.list_recent(limit=10)
    tasks = [r.task for r in recent]
    assert tasks == ["third", "second", "first"]


def test_list_recent_respects_limit(fake_redis):
    store = TaskStore(client=fake_redis)
    for i in range(5):
        store.save(TaskRecord(task=f"task-{i}", created_at=float(i)))

    recent = store.list_recent(limit=2)
    assert len(recent) == 2


def test_delete(fake_redis):
    store = TaskStore(client=fake_redis)
    record = TaskRecord(task="Do the thing")
    store.save(record)

    assert store.delete(record.task_id) is True
    assert store.get(record.task_id) is None
    assert store.delete(record.task_id) is False


def test_mark_failed(fake_redis):
    store = TaskStore(client=fake_redis)
    record = TaskRecord(task="Do the thing")
    store.save(record)

    updated = store.mark_failed(record.task_id, "boom")
    assert updated.status == TaskStatus.FAILED
    assert updated.error == "boom"

    fetched = store.get(record.task_id)
    assert fetched.status == TaskStatus.FAILED
    assert fetched.error == "boom"


def test_mark_failed_missing_task(fake_redis):
    store = TaskStore(client=fake_redis)
    assert store.mark_failed("does-not-exist", "boom") is None


def test_save_round_trips_trace(fake_redis):
    store = TaskStore(client=fake_redis)
    record = TaskRecord(task="Do the thing")
    record.trace.append(
        TraceEntry(agent=AgentName.PLANNER, input_summary="in", output="out", metadata={"foo": "bar"})
    )
    store.save(record)

    fetched = store.get(record.task_id)
    assert len(fetched.trace) == 1
    assert fetched.trace[0].agent == AgentName.PLANNER
    assert fetched.trace[0].metadata == {"foo": "bar"}
