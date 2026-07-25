# SPDX-License-Identifier: Apache-2.0
"""agent_spawn bridge tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.agents.runtime.subagent_ops import agent_list_payload, spawn_subagent_coordination
from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool


def test_agent_list_on_demand_only():
    payload = agent_list_payload()
    assert payload["agents"] == []
    assert payload["agent_count"] == 0
    assert payload["spawn_policy"]["on_demand_only"] is True
    assert payload["spawn_policy"]["mutation_execution_enabled"] is False


def test_agent_spawn_tool_requires_goal():
    out = execute_agent_tool("agent_spawn", {}, session_id="spawn-test")
    assert "goal_required" in out


def test_agent_spawn_delegates_to_coordination():
    fake = {
        "ok": True,
        "plan": {"plan_id": "plan-test", "agent_count": 2},
        "results": [
            {"agent_id": "provider_ops", "task": "diag", "status": "completed", "summary": "ok"},
            {"agent_id": "operations_analyst", "task": "report", "status": "completed", "summary": "done"},
        ],
        "graph": {"nodes": [], "edges": [], "replay": []},
        "merged": {"status": "completed"},
        "report": "# Report",
        "coordination_artifact_id": "art-coord",
        "summary_artifact_id": "art-sum",
        "duration_ms": 10,
    }
    with patch("aethos_core.agents.runtime.subagent_ops._run_coordination", return_value=fake):
        payload = spawn_subagent_coordination(goal="analyze why railway deployment failed", session_id="s")
    assert payload["ok"] is True
    assert len(payload["transcript"]) == 2
    assert payload["transcript"][1]["received_from_prior"][0]["from_agent"] == "provider_ops"


def test_agent_list_tool_json():
    out = execute_agent_tool("agent_list", {}, session_id="list-test")
    assert "on_demand_only" in out
    assert '"agents": []' in out or "'agents': []" in out
