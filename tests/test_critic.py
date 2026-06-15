"""Tests for app.agents.critic._parse_verdict."""

from __future__ import annotations

from app.agents.critic import _parse_verdict


def test_parse_plain_json_approved():
    approved, feedback = _parse_verdict('{"approved": true, "feedback": "Looks good"}')
    assert approved is True
    assert feedback == "Looks good"


def test_parse_plain_json_rejected():
    approved, feedback = _parse_verdict('{"approved": false, "feedback": "Needs more detail"}')
    assert approved is False
    assert feedback == "Needs more detail"


def test_parse_fenced_json():
    raw = '```json\n{"approved": false, "feedback": "Expand section 2"}\n```'
    approved, feedback = _parse_verdict(raw)
    assert approved is False
    assert feedback == "Expand section 2"


def test_parse_non_json_defaults_to_rejected():
    approved, feedback = _parse_verdict("This is not JSON at all")
    assert approved is False
    assert "not JSON" in feedback


def test_parse_missing_feedback_field():
    approved, feedback = _parse_verdict('{"approved": true}')
    assert approved is True
    assert feedback == "No feedback provided."
