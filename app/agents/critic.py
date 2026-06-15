"""Critic agent: reviews the draft and decides approve vs. request revision.

NOTE: Stage 2 placeholder. Stage 3 replaces the *judgment* (currently a
trivial heuristic) with a real LLM call. The revision-counting and state
update contract here is final and matches what app.core.graph.route_after_critic
expects.
"""

from __future__ import annotations

import time

from app.agents.common import make_trace_entry, truncate
from app.core.state import WorkflowState
from app.models.schemas import AgentName


def critic_node(state: WorkflowState) -> dict:
    started_at = time.time()
    draft = state.get("draft", "")
    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 2)

    # Placeholder heuristic: approve once we've already done at least one
    # revision pass, or immediately if max_revisions is 0. Stage 3 replaces
    # this with an LLM-based quality judgment.
    approved = revision_count >= max_revisions or revision_count >= 1

    if approved:
        critique = "[PLACEHOLDER CRITIQUE] Draft looks acceptable. Approved."
    else:
        critique = (
            "[PLACEHOLDER CRITIQUE] Draft needs more detail in the research "
            "section. Please expand."
        )

    entry = make_trace_entry(
        agent=AgentName.CRITIC,
        input_summary=truncate(draft),
        output=critique,
        started_at=started_at,
        approved=approved,
        revision_count=revision_count,
    )

    update: dict = {
        "critique": critique,
        "critique_approved": approved,
        "trace": [entry],
    }

    if not approved:
        update["revision_count"] = revision_count + 1

    return update
