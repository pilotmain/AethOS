# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from aethos_core.operations.mutations.preflight import _discover_github_workflow_for_mutation
from aethos_core.operations.orchestration.provider_runtime import get_provider_api_token, resolve_execution_auth
from aethos_core.providers.github.shared.workflow_resolution import (
    resolve_latest_workflow_run,
    resolve_repository,
)


def test_resolve_repository_uses_find_by_name(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.providers.github.shared.workflow_resolution.find_repository_by_name",
        lambda token, name: {"full_name": "pilotmain/AethOS", "name": "AethOS"},
    )
    out = resolve_repository("token", repository="AethOS")
    assert out["ok"] is True
    assert out["full_name"] == "pilotmain/AethOS"


def test_railway_mutation_auth_fallback(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.providers.railway.auth.RailwayAuthAdapter.resolve_best_auth_method",
        lambda self, operation=None: {"method": "api_token", "credential_id": "cred-rw"},
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.auth.RailwayAuthAdapter.get_api_token",
        lambda self, cid: "rail-token" if cid == "cred-rw" else "",
    )
    monkeypatch.setattr(
        "aethos_core.connections.credential_runtime_gate.check_credential_gate",
        lambda credential_id, **kwargs: {"ok": True, "credential_id": credential_id},
    )
    auth = resolve_execution_auth(provider="railway", operation_type="restart", params={})
    token = get_provider_api_token(provider="railway", auth=auth)
    assert token == "rail-token"


def test_github_mutation_uses_shared_workflow_resolution(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.providers.github.shared.workflow_resolution.resolve_repository",
        lambda token, repository: {"ok": True, "full_name": "pilotmain/AethOS", "owner": "pilotmain", "repo": "AethOS"},
    )
    monkeypatch.setattr(
        "aethos_core.providers.github.shared.workflow_resolution.resolve_latest_workflow_run",
        lambda token, repository, limit=20, workflow_id=None, workflow_name=None: {
            "ok": True,
            "repository": repository,
            "workflow_id": 123,
            "workflow_name": "CI",
            "source_run_id": 456,
            "source_run_number": 7,
            "run": {"id": 456, "run_number": 7, "status": "completed"},
        },
    )
    monkeypatch.setattr(
        "aethos_core.providers.github.operations.mutations_api._attempt_rerun",
        lambda token, owner, repo, run_id: {"ok": True, "http_status": 201, "rerun_endpoint": "/rerun"},
    )
    monkeypatch.setattr(
        "aethos_core.providers.github.operations.mutations_api.fetch_workflow_runs",
        lambda token, repository, limit=10: {
            "ok": True,
            "runs": [{"id": 789, "status": "queued", "run_number": 8}],
        },
    )
    from aethos_core.providers.github.operations.mutations_api import rerun_latest_workflow

    result = rerun_latest_workflow(
        "token",
        repository="AethOS",
        workflow_resolution={
            "ok": True,
            "repository": "pilotmain/AethOS",
            "source_run_id": 456,
            "workflow_id": 123,
            "run": {"id": 456, "run_number": 7, "status": "completed"},
        },
    )
    assert result["ok"] is True
    assert result["rerun_attempted"] is True
    assert result["evidence"]["workflow_id"] == 123
    assert result["evidence"]["repository"] == "pilotmain/AethOS"


def test_preflight_github_workflow_discovery_integration(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth",
        lambda provider, operation_type, params: {"credential_id": "cred-gh", "auth_method": "api_token"},
    )
    monkeypatch.setattr(
        "aethos_core.providers.github.shared.workflow_resolution.discover_workflow_rerun_from_readonly_substrate",
        lambda repository, auth, limit=20, readonly_artifact=None: {
            "ok": True,
            "repository": repository,
            "workflow_name": "Deploy",
            "source_run_number": 3,
            "source_status": "completed",
            "run": {"id": 1},
        },
    )
    monkeypatch.setattr(
        "aethos_core.operations.orchestration.target_resolution.canonical_resolver.canonical_resolve_target",
        lambda **kwargs: type("R", (), {"status": "resolved", "target_name": "pilotmain/AethOS"})(),
    )
    monkeypatch.setattr(
        "aethos_core.providers.github.shared.readonly_workflow_artifact.find_recent_readonly_workflow_runs_artifact",
        lambda **kwargs: None,
    )
    out = _discover_github_workflow_for_mutation(
        target_name="pilotmain/AethOS",
        user_request="rerun latest workflow for AethOS",
    )
    assert out is not None
    assert out["repository"] == "pilotmain/AethOS"
