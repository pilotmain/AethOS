# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8E — Governed multi-agent orchestration runtime."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.agents.coordinator import simulate_task_graph
from aethos_core.agents.runtime.agent_limits import BLOCKED_AGENT_ACTIONS, MAX_AGENTS_PER_TASK
from aethos_core.agents.runtime.coordination import run_agent_coordination
from aethos_core.agents.runtime.planner import is_multi_agent_request, plan_task
from aethos_core.agents.runtime.registry import validate_agent_action
from aethos_core.chat.agent_intelligence import multi_agent_reply
from aethos_core.chat.lanes import is_deterministic_lane
from aethos_core.chat.service import resolve_chat_turn


@pytest.fixture
def agent_env(monkeypatch, tmp_path):
    artifacts = tmp_path / "agent_artifacts"
    registry = tmp_path / "lw_registry"
    lw_artifacts = tmp_path / "lw_artifacts"
    root = tmp_path / "repo"
    root.mkdir()
    (root / "aethos_core").mkdir()
    (root / "web" / "components").mkdir(parents=True)
    monkeypatch.setenv("AGENT_ARTIFACTS_DIR", str(artifacts))
    monkeypatch.setenv("LOCAL_WORKSPACE_REGISTRY_DIR", str(registry))
    monkeypatch.setenv("LOCAL_WORKSPACE_ARTIFACTS_DIR", str(lw_artifacts))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


def test_coordinator_cannot_self_authorize_mutation():
    graph = simulate_task_graph("ship feature safely")
    payload = graph.to_dict()
    assert payload["execution_enabled"] is False
    assert payload["dry_run"] is True
    assert any("mutation" in c.lower() for c in payload["verification_criteria"])


def test_agent_blocked_actions():
    assert "unrestricted_shell" in BLOCKED_AGENT_ACTIONS
    assert "self_spawn" in BLOCKED_AGENT_ACTIONS


def test_validate_agent_blocks_merge():
    result = validate_agent_action("code_intelligence", "merge")
    assert result["allowed"] is False


def test_plan_caps_agents():
    plan = plan_task("analyze why the latest Railway deployment failed")
    assert len(plan.assignments) <= MAX_AGENTS_PER_TASK
    assert any(a.agent_id == "provider_ops" for a in plan.assignments)


@pytest.mark.parametrize(
    "prompt",
    [
        "analyze why the latest Railway deployment failed",
        "analyze architecture risks in AethOS",
        "prepare a PR proposal for dependency modernization",
    ],
)
def test_multi_agent_prompts_deterministic_lane(prompt):
    assert is_multi_agent_request(prompt)
    assert is_deterministic_lane(prompt)


def test_coordination_produces_artifacts(agent_env):
    result = run_agent_coordination(
        goal="analyze architecture risks in AethOS",
        session_id="test",
        workspace_hint=str(agent_env),
    )
    assert result["ok"] is True
    assert result.get("coordination_artifact_id")
    assert result.get("mutation_execution_enabled") is False
    assert "Multi-agent operational intelligence report" in (result.get("report") or "") or "Architecture risk" in (result.get("report") or "")


def test_partial_failure_isolation(agent_env):
    result = run_agent_coordination(goal="analyze why vercel deployment failed", session_id="t")
    merged = result.get("merged") or {}
    assert merged.get("status") in ("completed", "partial", "failed")
    assert "timeline" in merged


def test_multi_agent_never_hits_llm(agent_env):
    with patch("aethos_core.provider.completion.complete_chat") as mock_llm:
        out = resolve_chat_turn("analyze why the latest Railway deployment failed", session_id="s1")
    mock_llm.assert_not_called()
    assert out.used_llm is False
    assert out.meta.get("multi_agent_route_selected") == "true"


def test_multi_agent_reply_metadata(agent_env):
    reply = multi_agent_reply("analyze why railway deployment failed", session_id="s2")
    assert reply is not None
    text, intent, meta = reply
    assert intent == "agent_coordination"
    assert meta["mutation_execution_enabled"] == "false"
    assert "operational report" in text.lower() or "failure analysis" in text.lower() or "Agent timeline" in text


def test_agents_api_list(agent_env):
    from fastapi.testclient import TestClient

    run_agent_coordination(goal="analyze architecture risks", session_id="api")
    from aethos_core.api.main import app

    client = TestClient(app)
    resp = client.get("/api/v1/agents")
    assert resp.status_code == 200
    body = resp.json()
    assert body["agents"] == []
    assert body["ok"] is True
