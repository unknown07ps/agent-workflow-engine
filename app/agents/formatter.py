"""Formatter agent: turns research + plan into a polished draft report.

NOTE: Stage 2 placeholder. Stage 3 replaces the body with a real LLM call.
"""

from __future__ import annotations

import time

from app.agents.common import make_trace_entry, truncate
from app.core.state import WorkflowState
from app.models.schemas import AgentName


def formatter_node(state: WorkflowState) -> dict:
    started_at = time.time()
    plan = state.get("plan", "")
    research = state.get("research", "")

    draft = (
        f"[PLACEHOLDER DRAFT]\n"
        f"# Report\n\n"
        f"## Plan\n{plan}\n\n"
        f"## Research\n{research}\n\n"
        f"## Conclusion\nThis is a placeholder draft."
    )

    entry = make_trace_entry(
        agent=AgentName.FORMATTER,
        input_summary=truncate(research),
        output=draft,
        started_at=started_at,
        revision_count=state.get("revision_count", 0),
    )

    return {"draft": draft, "trace": [entry]}
