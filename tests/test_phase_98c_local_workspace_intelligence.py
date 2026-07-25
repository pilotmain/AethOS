# SPDX-License-Identifier: Apache-2.0
"""Tests for Phase 9.8C — Local Workspace Intelligence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aethos_core.chat.local_workspace_prompts import local_workspace_reply
from aethos_core.local_workspace.mutations.foundation import BLOCKED_AUTONOMOUS_ACTIONS, GOVERNED_CODE_MUTATION_OPS
from aethos_core.local_workspace.registry import find_workspace_by_hint, list_workspaces, register_workspace
from aethos_core.local_workspace.readonly.actions import (
    run_architecture_report,
    run_dependency_report,
    run_git_status_report,
    run_workspace_scan,
)


@pytest.fixture
def workspace_intel_env(monkeypatch, tmp_path):
    registry = tmp_path / "registry"
    artifacts = tmp_path / "artifacts"
    root = tmp_path / "demo-repo"
    root.mkdir()
    (root / "package.json").write_text(json.dumps({"name": "demo", "dependencies": {"react": "^18.0.0"}}), encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (root / "aethos_core").mkdir()
    (root / "web" / "components").mkdir(parents=True)
    monkeypatch.setenv("LOCAL_WORKSPACE_REGISTRY_DIR", str(registry))
    monkeypatch.setenv("LOCAL_WORKSPACE_ARTIFACTS_DIR", str(artifacts))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


def test_register_workspace_persists_metadata(workspace_intel_env):
    repo = workspace_intel_env
    record = register_workspace(path=str(repo), name="Demo")
    assert record["workspace_id"].startswith("ws-")
    assert record["path"] == str(repo.resolve())
    assert record["stack"]["badges"]
    rows = list_workspaces()
    assert len(rows) == 1
    assert rows[0]["name"] == "Demo"


def test_workspace_scan_creates_artifact(workspace_intel_env):
    repo = workspace_intel_env
    result = run_workspace_scan(repo)
    assert result["ok"] is True
    artifact = result["artifact"]
    assert artifact["artifact_type"] == "local_repo_scan"
    assert artifact["read_only"] is True
    records_dir = workspace_intel_env.parent / "artifacts" / "records"
    assert (records_dir / f"{result['artifact']['artifact_id']}.json").is_file()


def test_architecture_analysis_detects_layers(workspace_intel_env):
    repo = workspace_intel_env
    result = run_architecture_report(hint=str(repo))
    analysis = result["analysis"]
    layer_names = {l["layer"] for l in analysis.get("layers") or []}
    assert len(layer_names) >= 1
    assert "Mission Control UI" in layer_names or "API layer" in layer_names or "Local workspace" in layer_names
    assert "Architecture analysis" in result["report"]


def test_dependency_report_readonly(workspace_intel_env):
    repo = workspace_intel_env
    result = run_dependency_report(hint=str(repo))
    assert result["analysis"]["read_only"] is True
    assert result["artifact"]["artifact_type"] == "dependency_audit"


def test_git_status_report_format(workspace_intel_env):
    repo = workspace_intel_env
    result = run_git_status_report(hint=str(repo))
    assert "Local git intelligence" in result["report"]
    assert "Writes blocked" in result["report"]


def test_chat_register_local_repo(workspace_intel_env):
    repo = workspace_intel_env
    reply = local_workspace_reply(f"register local repo {repo}")
    assert reply is not None
    text, intent, meta = reply
    assert intent == "workspace_registered"
    assert meta.get("read_only") == "true"
    assert "registered" in text.lower()


def test_chat_architecture_intent(workspace_intel_env):
    repo = workspace_intel_env
    register_workspace(path=str(repo), name="AethOS")
    reply = local_workspace_reply("analyze architecture of AethOS")
    assert reply is not None
    text, intent, _ = reply
    assert intent == "architecture_analysis"
    assert "Architecture" in text


def test_find_workspace_by_hint(workspace_intel_env):
    repo = workspace_intel_env
    register_workspace(path=str(repo), name="AethOS")
    found = find_workspace_by_hint("aethos")
    assert found is not None
    assert found["name"] == "AethOS"


def test_governed_mutation_foundation_blocks_autonomy():
    assert "unrestricted_shell" in BLOCKED_AUTONOMOUS_ACTIONS
    assert "auto_merge_main" in BLOCKED_AUTONOMOUS_ACTIONS
    assert "code_mutation_preflight" in GOVERNED_CODE_MUTATION_OPS


def test_workspaces_api_register_and_list(workspace_intel_env):
    from aethos_core.api.main import app

    repo = workspace_intel_env
    client = TestClient(app)
    reg = client.post("/api/v1/workspaces/register", json={"path": str(repo), "name": "API Demo"})
    assert reg.status_code == 200
    body = reg.json()
    assert body["ok"] is True
    assert body["workspace"]["name"] == "API Demo"

    listing = client.get("/api/v1/workspaces")
    assert listing.status_code == 200
    assert len(listing.json()["workspaces"]) >= 1

    ws_id = body["workspace"]["workspace_id"]
    arch = client.get(f"/api/v1/workspaces/{ws_id}/architecture")
    assert arch.status_code == 200
    assert "report" in arch.json()

    artifacts = client.get("/api/v1/workspaces/artifacts")
    assert artifacts.status_code == 200
    assert isinstance(artifacts.json()["artifacts"], list)


def test_artifacts_route_not_shadowed_by_workspace_id(workspace_intel_env):
    from aethos_core.api.main import app

    client = TestClient(app)
    resp = client.get("/api/v1/workspaces/artifacts")
    assert resp.status_code == 200
    assert resp.json().get("ok") is True


# ── Issue 1: governed read-only local-repo agent tools ──────────────────────────


def _exec(name, payload):
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    return json.loads(execute_agent_tool(name, payload, session_id="main", channel="chat"))


def test_repo_tools_registered_in_catalog():
    from aethos_core.execution_brain.agent_tool_catalog import list_model_facing_tool_names

    names = list_model_facing_tool_names()
    for tool in ("repo_overview", "repo_list", "repo_read", "repo_grep"):
        assert tool in names


def test_repo_overview_reads_registered_workspace(workspace_intel_env):
    repo = workspace_intel_env
    register_workspace(path=str(repo), name="pilotos")
    out = _exec("repo_overview", {"workspace": "pilotos"})
    assert out["ok"] is True
    assert out["name"] == repo.name
    assert "node" in out["stack"]["badges"] or "python" in out["stack"]["badges"]
    assert "react" in (out["dependencies"].get("node", {}).get("dependencies") or [])


def test_repo_list_bounded_and_scoped(workspace_intel_env):
    repo = workspace_intel_env
    register_workspace(path=str(repo), name="pilotos")
    out = _exec("repo_list", {"path": "pilotos", "max_depth": 2})
    assert out["ok"] is True
    assert "package.json" in out["entries"]


def test_repo_read_redacts_env_values(workspace_intel_env):
    repo = workspace_intel_env
    (repo / ".env").write_text("SECRET_KEY=supersecretvalue123\nPUBLIC=ok\n", encoding="utf-8")
    register_workspace(path=str(repo), name="pilotos")
    out = _exec("repo_read", {"path": str(repo / ".env")})
    assert out["ok"] is True
    assert "supersecretvalue123" not in out["content"]
    assert "***redacted***" in out["content"]


def test_repo_grep_finds_pattern(workspace_intel_env):
    repo = workspace_intel_env
    (repo / "main.py").write_text("def hi():\n    return 1  # TODO refine\n", encoding="utf-8")
    register_workspace(path=str(repo), name="pilotos")
    out = _exec("repo_grep", {"path": "pilotos", "pattern": "TODO"})
    assert out["ok"] is True
    assert out["count"] >= 1
    assert any("TODO" in m for m in out["matches"])


def test_repo_read_rejects_path_outside_registered_workspace(workspace_intel_env):
    repo = workspace_intel_env
    register_workspace(path=str(repo), name="pilotos")
    out = _exec("repo_read", {"path": "/etc/passwd"})
    assert out["ok"] is False
    assert out["error"] == "path_not_in_registered_workspace"


def test_repo_tools_error_when_nothing_registered(workspace_intel_env):
    out = _exec("repo_overview", {})
    assert out["ok"] is False
    assert out["error"] == "no_registered_workspaces"
