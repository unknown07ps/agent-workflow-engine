"""Shared pytest fixtures.

- `fake_redis`: an in-memory fakeredis client substituted for the real
  Redis connection, so tests don't need a running Redis server.
- `mock_llm`: patches app.agents.*.call_llm with deterministic fake
  responses so tests don't need a real ANTHROPIC_API_KEY or network access.
"""

from __future__ import annotations

import json
import os
import unittest.mock as mock

import pytest

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


@pytest.fixture()
def fake_redis(monkeypatch):
    """Provide an in-memory Redis substitute and patch get_redis_client to use it."""
    fakeredis = pytest.importorskip("fakeredis")
    client = fakeredis.FakeRedis(decode_responses=True)

    import app.core.store as store_module

    store_module.get_redis_client.cache_clear()
    monkeypatch.setattr(store_module, "get_redis_client", lambda: client)
    return client


@pytest.fixture()
def llm_responses():
    """Default canned responses for each agent role. Tests can override per-call."""
    return {
        "planner": "1. Sub-topic A\n2. Sub-topic B",
        "researcher": "Research findings about A and B.",
        "formatter": "# Report\n\nContent here.",
        "critic": json.dumps({"approved": True, "feedback": "Looks good"}),
    }


@pytest.fixture()
def mock_llm(llm_responses):
    """Patch call_llm in every agent module with a router based on system prompt.

    Reads from `llm_responses` directly (not a copy) so tests can mutate it
    (e.g. llm_responses["critic"] = [...]) even after this fixture is set up,
    as long as the mutation happens before the patched call_llm is invoked.
    """

    state = {"responses": llm_responses, "critic_calls": 0}

    def fake_call_llm(system_prompt, user_prompt, temperature=0.3):
        if "Planner" in system_prompt:
            return state["responses"]["planner"]
        if "Researcher" in system_prompt:
            return state["responses"]["researcher"]
        if "Formatter" in system_prompt:
            return state["responses"]["formatter"]
        if "Critic" in system_prompt:
            state["critic_calls"] += 1
            critic_resp = state["responses"]["critic"]
            if isinstance(critic_resp, list):
                idx = min(state["critic_calls"] - 1, len(critic_resp) - 1)
                return critic_resp[idx]
            return critic_resp
        return "unknown"

    patches = [
        mock.patch("app.agents.planner.call_llm", side_effect=fake_call_llm),
        mock.patch("app.agents.researcher.call_llm", side_effect=fake_call_llm),
        mock.patch("app.agents.formatter.call_llm", side_effect=fake_call_llm),
        mock.patch("app.agents.critic.call_llm", side_effect=fake_call_llm),
    ]
    for p in patches:
        p.start()

    yield state["responses"]

    for p in patches:
        p.stop()
