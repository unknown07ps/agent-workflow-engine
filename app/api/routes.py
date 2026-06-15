"""REST endpoints for the multi-agent workflow engine."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.config import settings
from app.core.runner import run_workflow
from app.core.store import TaskStore, healthcheck
from app.models.schemas import TaskRecord, TaskRequest, TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter()


def get_store() -> TaskStore:
    return TaskStore()


@router.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness/readiness probe, including Redis connectivity."""
    redis_ok = healthcheck()
    return {
        "status": "ok" if redis_ok else "degraded",
        "redis": redis_ok,
    }


@router.post("/tasks", status_code=status.HTTP_202_ACCEPTED, tags=["tasks"])
def create_task(request: TaskRequest, background_tasks: BackgroundTasks) -> dict:
    """Submit a new task. Runs asynchronously; poll GET /tasks/{task_id} for status."""
    if not request.task or not request.task.strip():
        raise HTTPException(status_code=422, detail="`task` must not be empty.")

    store = get_store()

    task_id = str(uuid.uuid4())
    max_revisions = request.max_revisions if request.max_revisions is not None else settings.max_critic_revisions

    record = TaskRecord(task_id=task_id, task=request.task, max_revisions=max_revisions)
    store.save(record)

    background_tasks.add_task(run_workflow, task_id, request.task, max_revisions, store)

    return {
        "task_id": task_id,
        "status": record.status,
        "message": "Task accepted. Poll GET /tasks/{task_id} for status and results.",
    }


@router.get("/tasks", tags=["tasks"])
def list_tasks(limit: int = 50) -> dict:
    """List recent tasks (most recent first)."""
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=422, detail="`limit` must be between 1 and 200.")

    store = get_store()
    records = store.list_recent(limit=limit)
    return {
        "count": len(records),
        "tasks": [_summarize(r) for r in records],
    }


@router.get("/tasks/{task_id}", tags=["tasks"])
def get_task(task_id: str) -> TaskRecord:
    """Fetch the full record for a task, including current status and any results."""
    store = get_store()
    record = store.get(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return record


@router.get("/tasks/{task_id}/trace", tags=["tasks"])
def get_task_trace(task_id: str) -> dict:
    """Fetch only the agent execution trace for a task."""
    store = get_store()
    record = store.get(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return {
        "task_id": record.task_id,
        "status": record.status,
        "revision_count": record.revision_count,
        "trace": record.trace,
    }


@router.get("/tasks/{task_id}/result", tags=["tasks"])
def get_task_result(task_id: str) -> dict:
    """Fetch only the final report for a task (404 if not yet completed)."""
    store = get_store()
    record = store.get(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    if record.status == TaskStatus.FAILED:
        raise HTTPException(status_code=500, detail=f"Task failed: {record.error}")

    if record.status != TaskStatus.COMPLETED or record.final_report is None:
        raise HTTPException(
            status_code=409,
            detail=f"Task is not yet completed (status={record.status}).",
        )

    return {
        "task_id": record.task_id,
        "status": record.status,
        "final_report": record.final_report,
    }


@router.delete("/tasks/{task_id}", tags=["tasks"])
def delete_task(task_id: str) -> dict:
    """Delete a task record."""
    store = get_store()
    deleted = store.delete(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return {"task_id": task_id, "deleted": True}


def _summarize(record: TaskRecord) -> dict:
    return {
        "task_id": record.task_id,
        "task": record.task,
        "status": record.status,
        "revision_count": record.revision_count,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }
