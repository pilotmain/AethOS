# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8C.1 — Engineering intent routing convergence."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.engineering_intelligence import (
    classify_engineering_intent,
    execute_engineering_intent,
    is_engineering_intelligence_request,
)
from aethos_core.chat.lanes import is_deterministic_lane
from aethos_core.chat.service import resolve_chat_turn


@pytest.fixture
def engineering_routing_env(monkeypatch, tmp_path):
    registry = tmp_path / "registry"
    artifacts = tmp_path / "artifacts"
    root = tmp_path / "demo-repo"
    root.mkdir()
    (root / "package.json").write_text('{"name":"demo","scripts":{"test":"vitest run"}}', encoding="utf-8")
    (root / "aethos_core").mkdir()
    (root / "web" / "components").mkdir(parents=True)
    monkeypatch.setenv("LOCAL_WORKSPACE_REGISTRY_DIR", str(registry))
    monkeypatch.setenv("LOCAL_WORKSPACE_ARTIFACTS_DIR", str(artifacts))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


@pytest.mark.parametrize(
    "prompt",
    [
        "register local repo /tmp/aethos",
        "show local repo status for AethOS",
        "analyze architecture of AethOS",
        "show dependency risks",
        "scan local workspace",
        "show branches for AethOS",
        "summarize diff for AethOS",
        "show failing tests",
        "scan workflows",
    ],
)
def test_engineering_prompts_are_deterministic_lane(prompt):
    assert is_engineering_intelligence_request(prompt), prompt
    assert is_deterministic_lane(prompt), prompt


def test_register_never_hits_llm(engineering_routing_env):
    repo = engineering_routing_env
    prompt = f"register local repo {repo}"
    with patch("aethos_core.provider.completion.complete_chat") as mock_llm:
        result = resolve_chat_turn(prompt, session_id="test-session")
    mock_llm.assert_not_called()
    assert result.used_llm is False
    assert result.intent == "workspace_registered"
    assert result.meta.get("engineering_route_selected") == "true"
    assert result.meta.get("fallback_used") == "false"
    assert "Workspace registered" in result.reply or "registered" in result.reply.lower()


def test_git_status_routing_metadata(engineering_routing_env):
    from aethos_core.local_workspace.registry import register_workspace

    repo = engineering_routing_env
    register_workspace(path=str(repo), name="AethOS")
    with patch("aethos_core.provider.completion.complete_chat") as mock_llm:
        result = resolve_chat_turn("show local repo status for AethOS", session_id="sess-1")
    mock_llm.assert_not_called()
    assert result.intent == "git_status_snapshot"
    assert result.meta.get("engineering_intent_type") == "git_status"
    assert "Local git intelligence" in result.reply


def test_architecture_executes_substrate_not_llm(engineering_routing_env):
    from aethos_core.local_workspace.registry import register_workspace

    repo = engineering_routing_env
    register_workspace(path=str(repo), name="AethOS")
    with patch("aethos_core.provider.completion.complete_chat") as mock_llm:
        result = resolve_chat_turn("analyze architecture of AethOS", session_id="sess-1")
    mock_llm.assert_not_called()
    assert result.intent == "architecture_analysis"
    assert "Architecture analysis" in result.reply


def test_session_context_resolves_implicit_workspace(engineering_routing_env):
    from aethos_core.local_workspace.registry import register_workspace
    from aethos_core.local_workspace.session_context import set_active_workspace

    repo = engineering_routing_env
    record = register_workspace(path=str(repo), name="AethOS")
    set_active_workspace("sess-implicit", record)
    with patch("aethos_core.provider.completion.complete_chat") as mock_llm:
        result = resolve_chat_turn("show git status", session_id="sess-implicit")
    mock_llm.assert_not_called()
    assert result.meta.get("engineering_route_selected") == "true"


def test_classify_register_intent(engineering_routing_env):
    repo = engineering_routing_env
    classified = classify_engineering_intent(f"register local repo {repo}")
    assert classified is not None
    assert classified.intent.value == "workspace_registration"
    assert classified.path == str(repo)


def test_execute_always_returns_for_classified_intent(engineering_routing_env):
    repo = engineering_routing_env
    out = execute_engineering_intent(f"register local repo {repo}", session_id="x")
    assert out is not None
    assert out[2]["fallback_used"] == "false"
