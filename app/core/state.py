"""State schema for the LangGraph workflow graph.

LangGraph operates on a TypedDict (or dataclass/pydantic model) that is passed
between nodes. Each node receives the current state, does its work, and returns
a partial dict of updates that LangGraph merges into the state.
"""

from __future__ import annotations

from typing import Annotated, Any, Optional, TypedDict

from app.models.schemas import TraceEntry


def _append(existing: list[Any], new: list[Any]) -> list[Any]:
    """Reducer used to append trace entries rather than overwrite the list."""
    return existing + new


class WorkflowState(TypedDict, total=False):
    """The full state object threaded through the agent graph.

    Fields:
        task_id: Identifier for the originating task record (Redis key).
        task: The original natural-language task description.
        max_revisions: Max number of critic->researcher/formatter revision loops.
        revision_count: How many revision loops have occurred so far.

        plan: Output of the Planner agent.
        research: Output of the Researcher agent.
        draft: Latest formatted draft produced by the Formatter agent.
        critique: Latest feedback from the Critic agent.
        critique_approved: Whether the Critic approved the current draft.

        final_report: The final, approved output.
        trace: Append-only list of TraceEntry records (one per agent step).
        error: Set if a node raises/handles an error, used to short-circuit the graph.
    """

    task_id: str
    task: str
    max_revisions: int
    revision_count: int

    plan: Optional[str]
    research: Optional[str]
    draft: Optional[str]
    critique: Optional[str]
    critique_approved: bool

    final_report: Optional[str]
    trace: Annotated[list[TraceEntry], _append]
    error: Optional[str]


def initial_state(task_id: str, task: str, max_revisions: int = 2) -> WorkflowState:
    """Build the initial state dict for a new workflow run."""
    return WorkflowState(
        task_id=task_id,
        task=task,
        max_revisions=max_revisions,
        revision_count=0,
        plan=None,
        research=None,
        draft=None,
        critique=None,
        critique_approved=False,
        final_report=None,
        trace=[],
        error=None,
    )
