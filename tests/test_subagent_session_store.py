# SPDX-License-Identifier: Apache-2.0
"""Subagent session store, agent_send, and governed terminal job tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.agents.runtime.cursor_terminal_jobs import create_governed_terminal_preflight
from aethos_core.agents.runtime.subagent_ops import (
    agent_sessions_list_payload,
    send_subagent_message,
    spawn_subagent_coordination,
)
from aethos_core.agents.runtime.subagent_session_store import (
    build_subagent_session_key,
    clear_subagent_sessions_for_tests,
    get_subagent_session,
    is_subagent_session_key,
    list_subagent_sessions,
)
from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool
from aethos_core.workspace_runtime.workspace_policy import evaluate_command_policy


@pytest.fixture(autouse=True)
def _clean_store(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_ARTIFACTS_DIR", str(tmp_path / "agent_artifacts"))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    clear_subagent_sessions_for_tests()
    yield
    clear_subagent_sessions_for_tests()
    get_settings.cache_clear()


FAKE_COORD = {
    "ok": True,
    "plan": {"plan_id": "plan-abc", "agent_count": 2},
    "results": [
        {"agent_id": "code_intelligence", "task": "scan", "status": "completed", "summary": "scan ok"},
        {"agent_id": "operations_analyst", "task": "report", "status": "completed", "summary": "report ok"},
    ],
    "graph": {"nodes": [], "edges": [], "replay": []},
    "merged": {"status": "completed"},
    "report": "# Multi-agent report\n\nDone.",
    "coordination_artifact_id": "art-1",
    "summary_artifact_id": "art-2",
    "duration_ms": 5,
}


def test_session_key_format():
    key = build_subagent_session_key(parent_session_id="operator", spawn_id="spawn-deadbeef")
    assert key == "agent:operator:subagent:spawn-deadbeef"
    assert is_subagent_session_key(key)


def test_spawn_persists_session():
    with patch("aethos_core.agents.runtime.subagent_ops._run_coordination", return_value=FAKE_COORD):
        out = spawn_subagent_coordination(goal="analyze architecture risks in AethOS", session_id="operator")
    assert out["ok"] is True
    assert out.get("session_key")
    row = get_subagent_session(out["session_key"])
    assert row is not None
    assert row["parent_session_id"] == "operator"
    assert len(row["messages"]) >= 2
    assert row["run_count"] == 1


def test_agent_send_follow_up_increments_run():
    with patch("aethos_core.agents.runtime.subagent_ops._run_coordination", return_value=FAKE_COORD):
        first = spawn_subagent_coordination(goal="analyze why railway deployment failed", session_id="op")
    key = first["session_key"]
    with patch("aethos_core.agents.runtime.subagent_ops._run_coordination", return_value=FAKE_COORD):
        second = send_subagent_message(
            message="focus on build logs only",
            session_id="op",
            session_key=key,
        )
    assert second["ok"] is True
    assert second.get("follow_up") is True
    assert second.get("run_count") == 2
    row = get_subagent_session(key)
    assert row["run_count"] == 2
    assert any(m.get("source_tool") == "agent_send" for m in row["messages"])


def test_agent_sessions_list_tool():
    with patch("aethos_core.agents.runtime.subagent_ops._run_coordination", return_value=FAKE_COORD):
        spawn_subagent_coordination(goal="multi-agent operational report for aethos", session_id="sess-a")
    payload = agent_sessions_list_payload(parent_session_id="sess-a")
    assert payload["session_count"] >= 1
    out = execute_agent_tool("agent_sessions_list", {"parent_session_id": "sess-a"}, session_id="sess-a")
    assert "session_key" in out


def test_terminal_create_preflight_allowlists_cursor():
    policy = evaluate_command_policy("cursor /tmp/aethos")
    assert policy.get("allowed") is True
    out = create_governed_terminal_preflight(command="git status", session_id="dev")
    assert out.get("preflight_id", "").startswith("tpf-")
    assert out.get("approval_required") is True
    assert out.get("autonomous_execution_blocked") is True


def test_terminal_tool_json():
    out = execute_agent_tool(
        "terminal_create_preflight",
        {"command": "git status", "workspace_hint": "aethos"},
        session_id="term-test",
    )
    assert "tpf-" in out
