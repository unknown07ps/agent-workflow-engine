"""Data models shared across the workflow engine."""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentName(str, Enum):
    PLANNER = "planner"
    RESEARCHER = "researcher"
    CRITIC = "critic"
    FORMATTER = "formatter"


class TraceEntry(BaseModel):
    """A single record of an agent's execution within the workflow."""

    agent: AgentName
    input_summary: str
    output: str
    started_at: float = Field(default_factory=time.time)
    finished_at: Optional[float] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.finished_at is None:
            return None
        return round(self.finished_at - self.started_at, 4)


class TaskRequest(BaseModel):
    """Incoming request to create a new workflow task."""

    task: str = Field(..., description="Natural language description of the task to perform.")
    max_revisions: Optional[int] = Field(
        default=None, description="Override the default critic revision limit for this task."
    )


class TaskRecord(BaseModel):
    """Persisted record of a task's full lifecycle, stored in Redis."""

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task: str
    status: TaskStatus = TaskStatus.PENDING
    max_revisions: int = 2

    plan: Optional[str] = None
    research: Optional[str] = None
    critique: Optional[str] = None
    final_report: Optional[str] = None

    revision_count: int = 0
    trace: list[TraceEntry] = Field(default_factory=list)

    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    def touch(self) -> None:
        self.updated_at = time.time()
