# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.chat.llm_developer_subagent_lane import (
    is_llm_developer_spawn_request,
    llm_developer_subagent_reply,
)
from aethos_core.execution_brain.agent_runtime import AgentRuntimeResult


def test_llm_developer_spawn_pattern():
    assert is_llm_developer_spawn_request("agent_spawn llm developer: scan providers")
    assert not is_llm_developer_spawn_request("agent_spawn analyze deployment")


@patch("aethos_core.agents.runtime.subagent_ops.spawn_llm_developer_subagent")
def test_llm_developer_lane_reply(mock_spawn):
    mock_spawn.return_value = {
        "ok": True,
        "session_key": "agent:default:subagent:llmdev-abc",
        "spawn_id": "llmdev-abc",
        "reply": "Providers look healthy.",
        "tool_calls": 2,
    }
    handled = llm_developer_subagent_reply(
        "agent_spawn llm developer: quick scan all providers",
        session_id="default",
    )
    assert handled is not None
    body, intent, meta = handled
    assert intent == "llm_developer_spawn"
    assert "session_key" in body
    assert meta.get("session_key") == "agent:default:subagent:llmdev-abc"


@patch("aethos_core.execution_brain.agent_runtime.run_agent_runtime_turn")
def test_spawn_llm_developer_subagent(mock_runtime):
    from aethos_core.agents.runtime.subagent_ops import spawn_llm_developer_subagent
    from aethos_core.agents.runtime.subagent_session_store import clear_subagent_sessions_for_tests

    clear_subagent_sessions_for_tests()
    mock_runtime.return_value = AgentRuntimeResult(
        reply="Done.",
        used_llm=True,
        tool_calls=1,
        provider="anthropic",
        model="claude",
    )
    out = spawn_llm_developer_subagent(goal="scan pytest failures", session_id="dev")
    assert out["ok"] is True
    assert out["session_key"].startswith("agent:dev:subagent:")
    clear_subagent_sessions_for_tests()
