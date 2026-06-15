"""Researcher agent: gathers information based on the plan (and any critique).

NOTE: Stage 2 placeholder. Stage 3 replaces the body with a real LLM call.
"""

from __future__ import annotations

import time

from app.agents.common import make_trace_entry, truncate
from app.core.state import WorkflowState
from app.models.schemas import AgentName


def researcher_node(state: WorkflowState) -> dict:
    started_at = time.time()
    plan = state.get("plan", "")
    critique = state.get("critique")

    if critique:
        research = (
            f"[PLACEHOLDER RESEARCH - revision]\n"
            f"Addressing critique: {critique}\n"
            f"Additional findings based on plan:\n{plan}"
        )
    else:
        research = f"[PLACEHOLDER RESEARCH]\nFindings based on plan:\n{plan}"

    entry = make_trace_entry(
        agent=AgentName.RESEARCHER,
        input_summary=truncate(plan if not critique else f"plan + critique: {critique}"),
        output=research,
        started_at=started_at,
        revision_count=state.get("revision_count", 0),
    )

    return {"research": research, "trace": [entry]}
