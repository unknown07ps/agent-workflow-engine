"""Tests for app.core.graph and app.core.state."""

from __future__ import annotations

import json

from app.core.graph import build_graph, route_after_critic, route_if_error
from app.core.state import initial_state


def test_initial_state_shape():
    state = initial_state("task-1", "Do the thing", max_revisions=3)
    assert state["task_id"] == "task-1"
    assert state["task"] == "Do the thing"
    assert state["max_revisions"] == 3
    assert state["revision_count"] == 0
    assert state["trace"] == []
    assert state["critique_approved"] is False


def test_route_after_critic_approved_ends():
    state = {"critique_approved": True, "revision_count": 0, "max_revisions": 2}
    assert route_after_critic(state) == "end"


def test_route_after_critic_rejected_revises():
    state = {"critique_approved": False, "revision_count": 0, "max_revisions": 2}
    assert route_after_critic(state) == "revise"


def test_route_after_critic_budget_exhausted_ends():
    state = {"critique_approved": False, "revision_count": 2, "max_revisions": 2}
    assert route_after_critic(state) == "end"


def test_route_after_critic_error_ends():
    state = {"error": "boom", "critique_approved": False, "revision_count": 0, "max_revisions": 2}
    assert route_after_critic(state) == "end"


def test_route_if_error_continues_without_error():
    router = route_if_error("next")
    assert router({"error": None}) == "next"
    assert router({}) == "next"


def test_route_if_error_short_circuits():
    router = route_if_error("next")
    assert router({"error": "boom"}) == "finalize"


def test_graph_full_run_approved_first_pass(mock_llm):
    graph = build_graph()
    state = initial_state("task-1", "Write a report on X", max_revisions=2)
    result = graph.invoke(state)

    assert result["error"] is None
    assert result["final_report"] == "# Report\n\nContent here."
    assert result["revision_count"] == 0

    agents = [t.agent.value for t in result["trace"]]
    assert agents == ["planner", "researcher", "formatter", "critic"]


def test_graph_full_run_with_revision(mock_llm, llm_responses):
    # First critic call rejects, second approves.
    llm_responses["critic"] = [
        json.dumps({"approved": False, "feedback": "Add more detail"}),
        json.dumps({"approved": True, "feedback": "Looks good now"}),
    ]

    graph = build_graph()
    state = initial_state("task-1", "Write a report on X", max_revisions=2)
    result = graph.invoke(state)

    assert result["final_report"] == "# Report\n\nContent here."
    assert result["revision_count"] == 1

    agents = [t.agent.value for t in result["trace"]]
    assert agents == [
        "planner",
        "researcher",
        "formatter",
        "critic",
        "researcher",
        "formatter",
        "critic",
    ]


def test_graph_revision_budget_exhausted(mock_llm, llm_responses):
    # Critic always rejects.
    llm_responses["critic"] = json.dumps({"approved": False, "feedback": "Never good enough"})

    graph = build_graph()
    state = initial_state("task-1", "Write a report on X", max_revisions=1)
    result = graph.invoke(state)

    # After 1 rejection, revision_count reaches max_revisions and the router
    # ends the graph directly (without re-invoking the critic), shipping the
    # best-effort draft as final_report.
    assert result["final_report"] == "# Report\n\nContent here."
    assert result["revision_count"] == 1
    assert result["critique_approved"] is False
    agents = [t.agent.value for t in result["trace"]]
    assert agents == ["planner", "researcher", "formatter", "critic"]


def test_graph_max_revisions_zero_forces_approval(mock_llm, llm_responses):
    llm_responses["critic"] = json.dumps({"approved": False, "feedback": "bad"})

    graph = build_graph()
    result = graph.invoke(initial_state("task-1", "Write a report on X", max_revisions=0))

    assert result["revision_count"] == 0
    assert result["critique_approved"] is True
    assert "exhausted" in result["critique"].lower()
    assert result["final_report"] == "# Report\n\nContent here."
    agents = [t.agent.value for t in result["trace"]]
    assert agents == ["planner", "researcher", "formatter", "critic"]


def test_graph_short_circuits_on_planner_error(mock_llm, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr("app.agents.planner.call_llm", boom)

    graph = build_graph()
    state = initial_state("task-1", "Write a report on X", max_revisions=2)
    result = graph.invoke(state)

    assert result["error"] == "LLM unavailable"
    assert result["final_report"] is None
    agents = [t.agent.value for t in result["trace"]]
    assert agents == ["planner"]
