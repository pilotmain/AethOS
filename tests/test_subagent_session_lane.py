# SPDX-License-Identifier: Apache-2.0
"""Subagent session chat lane — spawn/send before generic multi-agent routing."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.subagent_session_lane import (
    is_subagent_send_request,
    is_subagent_spawn_request,
    subagent_session_reply,
)


FAKE_SPAWN = {
    "ok": True,
    "spawn_id": "spawn-abc",
    "session_key": "agent:sess-1:subagent:spawn-abc",
    "plan_id": "plan-1",
    "report_excerpt": "# Report\n\nRoot cause found.",
    "status": "completed",
}

FAKE_COORD = {
    "ok": True,
    "plan": {"plan_id": "plan-2", "agent_count": 1},
    "results": [],
    "graph": {},
    "merged": {"status": "completed"},
    "report": "focused report",
    "duration_ms": 1,
}


@pytest.fixture(autouse=True)
def _clean_store(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_ARTIFACTS_DIR", str(tmp_path / "agent_artifacts"))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.agents.runtime.subagent_session_store import clear_subagent_sessions_for_tests

    clear_subagent_sessions_for_tests()
    yield
    clear_subagent_sessions_for_tests()
    get_settings.cache_clear()


def test_spawn_intent_detected():
    assert is_subagent_spawn_request("agent_spawn multi-agent analysis for vercel — save session_key")
    assert not is_subagent_spawn_request("analyze why railway deployment failed")


def test_send_intent_detected():
    assert is_subagent_send_request("agent_send to that session: focus on Root Directory only")


def test_spawn_lane_returns_session_key():
    with patch("aethos_core.agents.runtime.subagent_ops.spawn_subagent_coordination", return_value=FAKE_SPAWN):
        out = subagent_session_reply(
            "agent_spawn multi-agent analysis for aethos Vercel failures — save session_key",
            session_id="sess-ptneh2d5",
        )
    assert out is not None
    body, intent, meta = out
    assert intent == "subagent_spawn"
    assert "agent:sess-1:subagent:spawn-abc" in body
    assert meta.get("session_key") == "agent:sess-1:subagent:spawn-abc"


def test_send_lane_uses_latest_session():
    with patch("aethos_core.agents.runtime.subagent_ops._run_coordination", return_value=FAKE_COORD):
        subagent_session_reply(
            "agent_spawn analyze vercel failures — save session_key",
            session_id="sess-a",
        )
    with patch("aethos_core.agents.runtime.subagent_ops._run_coordination", return_value=FAKE_COORD):
        out = subagent_session_reply(
            "agent_send to that session: focus on Root Directory only",
            session_id="sess-a",
        )
    assert out is not None
    body, intent, meta = out
    assert intent == "subagent_send"
    assert meta.get("session_key")


def test_spawn_runs_before_multi_agent_lane():
    """Regression: agent_spawn must not lose session_key to bare multi_agent_reply."""
    from aethos_core.agents.runtime.planner import is_multi_agent_request

    prompt = "agent_spawn multi-agent analysis for aethos Vercel failures — save session_key"
    assert is_multi_agent_request(prompt)
    assert is_subagent_spawn_request(prompt)
