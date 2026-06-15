"""Shared helpers used by all agent node implementations."""

from __future__ import annotations

import time
from typing import Any

from app.models.schemas import AgentName, TraceEntry


def make_trace_entry(
    agent: AgentName,
    input_summary: str,
    output: str,
    started_at: float,
    **metadata: Any,
) -> TraceEntry:
    """Build a completed TraceEntry for appending to state['trace']."""
    return TraceEntry(
        agent=agent,
        input_summary=input_summary,
        output=output,
        started_at=started_at,
        finished_at=time.time(),
        metadata=metadata,
    )


def truncate(text: str | None, max_len: int = 500) -> str:
    """Truncate text for use in trace input summaries."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "... [truncated]"
