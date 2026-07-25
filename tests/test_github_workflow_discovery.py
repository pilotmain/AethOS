# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow discovery tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
    compose_rerun_no_execution_followup,
)
from aethos_core.providers.github.workflow_discovery.actions_enablement_checker import check_actions_enablement
from aethos_core.providers.github.workflow_discovery.workflow_discovery_reply import compose_workflow_discovery_reply
from aethos_core.providers.github.workflow_discovery.workflow_file_discovery import discover_workflow_files
from aethos_core.providers.github.workflow_discovery.workflow_run_absence_diagnosis import (
    diagnose_workflow_run_absence,
)
from aethos_core.providers.github.workflow_discovery.workflow_trigger_analyzer import analyze_workflow_triggers


def _repo_resolve():
    return {"ok": True, "owner": "pilotmain", "repo": "aethos", "full_name": "pilotmain/aethos", "default_branch": "main"}


def test_workflows_directory_missing() -> None:
    with patch(
        "aethos_core.providers.github.workflow_discovery.workflow_file_discovery.resolve_repository",
        return_value=_repo_resolve(),
    ), patch(
        "aethos_core.providers.github.workflow_discovery.workflow_file_discovery.request_github",
        return_value={"ok": False, "http_status": 404, "error": "Not Found"},
    ):
        result = discover_workflow_files("token", repository="pilotmain/aethos")
    assert result["workflows_dir_found"] is False
    assert result["workflow_file_names"] == []


def test_workflow_files_exist_but_no_runs_diagnosis() -> None:
    workflow_yaml = "name: CI\non:\n  push:\n    branches: [main]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
    with patch(
        "aethos_core.providers.github.workflow_discovery.workflow_run_absence_diagnosis.discover_workflow_files",
        return_value={
            "ok": True,
            "repository": "pilotmain/aethos",
            "default_branch": "main",
            "ref": "main",
            "workflows_dir_found": True,
            "workflow_file_names": ["ci.yml"],
            "workflow_files": [{"name": "ci.yml", "content": workflow_yaml, "ok": True}],
        },
    ), patch(
        "aethos_core.providers.github.workflow_discovery.workflow_run_absence_diagnosis.check_actions_enablement",
        return_value={
            "ok": True,
            "actions_status": "enabled",
            "actions_enabled": True,
            "registered_workflow_count": 1,
            "disabled_workflow_count": 0,
            "permissions_readable": True,
            "workflows_api_readable": True,
        },
    ), patch(
        "aethos_core.providers.github.workflow_discovery.workflow_run_absence_diagnosis.github_discovery_auth_diagnostics",
        return_value={"auth_state": "validated", "workflow_scope_present": False},
    ), patch(
        "aethos_core.providers.github.workflow_discovery.workflow_run_absence_diagnosis.fetch_branch_status",
        return_value={"ok": True, "branch": "main", "sha": "abc123"},
    ), patch(
        "aethos_core.providers.github.workflow_discovery.workflow_run_absence_diagnosis.fetch_recent_commits",
        return_value={"ok": True, "commits": [{"sha": "abc123", "message": "fix", "author": "raya"}]},
    ):
        diagnosis = diagnose_workflow_run_absence("token", repository="pilotmain/aethos")
    assert diagnosis["workflows_dir_found"] is True
    assert "push" in diagnosis["trigger_analysis"]["all_triggers"]
    assert "workflow run" in diagnosis["likely_reason"].lower()
    reply = compose_workflow_discovery_reply(diagnosis)
    assert ".github/workflows/" in reply
    assert "ci.yml" in reply
    assert "Next steps:" in reply


def test_workflow_dispatch_exists() -> None:
    content = "name: Deploy\non:\n  workflow_dispatch:\njobs:\n  deploy:\n    runs-on: ubuntu-latest\n"
    analysis = analyze_workflow_triggers(content, filename="deploy.yml")
    assert analysis["has_workflow_dispatch"] is True
    assert "workflow_dispatch" in analysis["triggers"]


def test_workflows_disabled() -> None:
    with patch(
        "aethos_core.providers.github.workflow_discovery.actions_enablement_checker.resolve_repository",
        return_value=_repo_resolve(),
    ), patch(
        "aethos_core.providers.github.workflow_discovery.actions_enablement_checker.request_github",
        side_effect=[
            {"ok": True, "data": {"enabled": False, "allowed_actions": "all"}},
            {"ok": True, "data": {"workflows": [{"id": 1, "name": "CI", "state": "disabled", "path": ".github/workflows/ci.yml"}]}},
        ],
    ):
        result = check_actions_enablement("token", repository="pilotmain/aethos")
    assert result["actions_status"] == "disabled"


def test_actions_api_permission_missing() -> None:
    with patch(
        "aethos_core.providers.github.workflow_discovery.actions_enablement_checker.resolve_repository",
        return_value=_repo_resolve(),
    ), patch(
        "aethos_core.providers.github.workflow_discovery.actions_enablement_checker.request_github",
        side_effect=[
            {"ok": False, "http_status": 403, "error": "HTTP 403"},
            {"ok": False, "http_status": 403, "error": "HTTP 403"},
        ],
    ):
        result = check_actions_enablement("token", repository="pilotmain/aethos")
    assert result["actions_status"] == "unknown_permission"


def test_rerun_noop_includes_discovery_explanation() -> None:
    from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests
    from aethos_core.runtime.authority import authority

    clear_github_context_for_tests()
    authority.create_job(
        title="GitHub workflow rerun preflight",
        job_type="mutation_preflight",
        params={
            "provider": "github",
            "operation_type": "workflow_rerun",
            "session_id": "discovery-followup",
            "target_name": "pilotmain/aethos",
            "preflight_status": "needs_workflow_resolution",
            "discovery_failure_reason": "no_workflow_runs",
            "workflow_discovery": {
                "repository": "pilotmain/aethos",
                "workflows_dir_found": False,
                "workflow_file_names": [],
                "trigger_analysis": {"all_triggers": []},
                "actions_status": "unknown",
                "default_branch": "main",
                "likely_reason": "No `.github/workflows/` directory exists on the inspected branch — GitHub Actions workflows are not configured.",
                "next_steps": ["Add a workflow under `.github/workflows/` (for example `ci.yml`)."],
            },
        },
        source="test",
        session_id="discovery-followup",
        auto_run=False,
    )
    reply = compose_rerun_no_execution_followup("why no workflow runs?", session_id="discovery-followup")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "github_workflow_rerun_no_execution_followup"
    assert "workflow discovery" in body.lower()
    assert "not found" in body.lower()
    assert "execution job" not in body.lower()
    assert meta.get("rerun_executed") == "false"


def test_why_cant_rerun_uses_discovery() -> None:
    from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests
    from aethos_core.runtime.authority import authority

    clear_github_context_for_tests()
    authority.create_job(
        title="GitHub workflow rerun preflight",
        job_type="mutation_preflight",
        params={
            "provider": "github",
            "operation_type": "workflow_rerun",
            "session_id": "why-rerun",
            "target_name": "pilotmain/aethos",
            "preflight_status": "needs_workflow_resolution",
            "discovery_failure_reason": "no_workflow_runs",
            "workflow_discovery": {
                "repository": "pilotmain/aethos",
                "workflows_dir_found": True,
                "workflow_file_names": ["ci.yml"],
                "trigger_analysis": {"all_triggers": ["workflow_dispatch"], "has_workflow_dispatch": True},
                "actions_status": "enabled",
                "default_branch": "main",
                "likely_reason": "Workflows exist but only manual `workflow_dispatch` triggers were detected — no run has been dispatched yet.",
                "next_steps": ["Manually dispatch the workflow from GitHub Actions if `workflow_dispatch` is configured."],
            },
        },
        source="test",
        session_id="why-rerun",
        auto_run=False,
    )
    reply = compose_rerun_no_execution_followup("why can't rerun?", session_id="why-rerun")
    assert reply is not None
    body, _, _ = reply
    assert "workflow_dispatch" in body
    assert "No rerun is possible until a workflow run exists." in body
