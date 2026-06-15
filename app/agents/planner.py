"""Planner agent: breaks the user's task into a structured plan.

NOTE: This is a Stage 2 placeholder. Stage 3 replaces the body with a real
LLM call via app.core.llm_client. The signature and trace-recording contract
below are final and won't change.
"""

from __future__ import annotations

import time

from app.agents.common import make_trace_entry, truncate
from app.core.state import WorkflowState
from app.models.schemas import AgentName


def planner_node(state: WorkflowState) -> dict:
    started_at = time.time()
    task = state["task"]

    # Placeholder output - Stage 3 replaces this with an LLM-generated plan.
    plan = (
        f"[PLACEHOLDER PLAN]\n"
        f"1. Understand the task: {task}\n"
        f"2. Identify key sub-topics to research.\n"
        f"3. Draft a structured outline for the final report."
    )

    entry = make_trace_entry(
        agent=AgentName.PLANNER,
        input_summary=truncate(task),
        output=plan,
        started_at=started_at,
    )

    return {"plan": plan, "trace": [entry]}
