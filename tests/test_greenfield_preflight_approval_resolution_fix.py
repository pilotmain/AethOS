# SPDX-License-Identifier: Apache-2.0
"""Tests for GREENFIELD_PREFLIGHT_APPROVAL_RESOLUTION_FIX."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.jobs.job_approval_guidance import compose_job_approval_guidance_reply
from aethos_core.jobs.pending_job_approval_resolution import resolve_short_approval
from aethos_core.jobs.session_approval_target import (
    clear_session_approval_targets_for_tests,
    get_session_approval_target,
    list_active_session_approval_targets,
    record_session_approval_target,
)
from aethos_core.jobs.short_approval_intent import is_short_approval_intent
from aethos_core.provider_e2e_execution.job_taxonomy import PROVIDER_E2E_ORCHESTRATION_JOB_TYPE
from aethos_core.providers.railway.greenfield_deployment.greenfield_flow import run_railway_greenfield_deployment_flow
from aethos_core.providers.railway.greenfield_deployment.greenfield_preflight import (
    RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE,
)
from aethos_core.runtime.authority import authority
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store
from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests
from aethos_core.connections.validation_status import VALIDATED

_SECRET = "railway_greenfield_secret_token_1234567890"
_LIST_SERVICES_PATCH = "aethos_core.providers.railway.credential_truth.list_services_with_status"
_GREENFIELD_PROMPT = (
    "AethOS is a new project. Check local workspace, get its remote git, "
    "create a new Railway project, deploy, set required env vars, and report back."
)


@pytest.fixture(autouse=True)
def _isolate_jobs():
    from aethos_core.providers.github.workflow_lane.workflow_lane_router import clear_for_tests as clear_workflow_lane_for_tests

    job_store.clear_for_tests()
    job_executor.drain_queue_for_tests()
    clear_session_approval_targets_for_tests()
    clear_workflow_lane_for_tests()
    yield
    job_store.clear_for_tests()
    job_executor.drain_queue_for_tests()
    clear_session_approval_targets_for_tests()
    clear_workflow_lane_for_tests()


@pytest.fixture
def vault_paths(tmp_path, monkeypatch):
    cred_dir = tmp_path / "credentials"
    monkeypatch.setenv("CREDENTIALS_DIR", str(cred_dir))
    monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
    reset_credential_vault_for_tests()
    get_settings.cache_clear()
    settings = get_settings()
    monkeypatch.setattr(settings, "railway_api_token", "")
    yield cred_dir
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


@pytest.fixture
def local_repo(tmp_path):
    repo = tmp_path / "AethOS"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname = 'aethos'\n", encoding="utf-8")
    (repo / ".env.example").write_text("ANTHROPIC_API_KEY=\nDATABASE_URL=\nPORT=8010\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "ops@example.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "AethOS Test"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:pilotmain/AethOS.git"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return repo


def _store_validated(vault_paths) -> None:
    vault = CredentialVault(vault_paths)
    rec = vault.store_api_token(provider="railway", label="Railway primary", token=_SECRET)
    vault.mark_validation_result(rec.credential_id, status=VALIDATED, ok=True)
    reset_credential_vault_for_tests()
    CredentialVault(vault_paths)


def _inventory_ok(token, *args, **kwargs):
    _ = (token, args, kwargs)
    return {"ok": True, "services": [], "error": None}


def _run_greenfield_preflight(vault_paths, local_repo, monkeypatch, session_id: str):
    _store_validated(vault_paths)
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "true")
    monkeypatch.setenv("PROVIDER_ENV_VAR_MUTATIONS_ENABLED", "true")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.local_workspace_source.resolve_configured_workspace_root",
        lambda: local_repo,
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        lambda: ("token", "test", None),
    )
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        return run_railway_greenfield_deployment_flow(_GREENFIELD_PROMPT, session_id=session_id)


def test_short_approval_intent_detection():
    assert is_short_approval_intent("approve")
    assert is_short_approval_intent("yes approve")
    assert is_short_approval_intent("go ahead")
    assert is_short_approval_intent("run it")
    assert is_short_approval_intent(f"approve job-abc123")
    assert not is_short_approval_intent("where do i approve job-abc123?")
    assert not is_short_approval_intent("show Railway projects")


def test_greenfield_preflight_stores_session_approval_target(vault_paths, local_repo, monkeypatch):
    result = _run_greenfield_preflight(vault_paths, local_repo, monkeypatch, session_id="gf-memory")
    assert result.ok is True

    targets = list_active_session_approval_targets(session_id="gf-memory")
    assert len(targets) == 1
    target = targets[0]
    assert target.latest_pending_job_id == result.preflight_job_id
    assert target.job_type == RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE
    assert target.provider == "railway"
    assert target.action_type == "create_project_service_env_deploy_verify"
    assert target.preflight_id.startswith("rgf-")
    assert target.approval_route.endswith("/approve-railway-greenfield-preflight")
    assert target.mutation_performed is False


def test_no_mutation_before_approval(vault_paths, local_repo, monkeypatch):
    result = _run_greenfield_preflight(vault_paths, local_repo, monkeypatch, session_id="gf-no-mut")
    job = job_store.get(result.preflight_job_id)
    assert job is not None
    assert job.params.get("mutation_performed") is False
    assert job.params.get("greenfield_preflight_approved") is None


def test_approve_after_greenfield_resolves_stored_job(vault_paths, local_repo, monkeypatch):
    result = _run_greenfield_preflight(vault_paths, local_repo, monkeypatch, session_id="gf-approve")
    approve_patch = (
        "aethos_core.providers.railway.greenfield_deployment.greenfield_approval_flow."
        "approve_railway_greenfield_preflight"
    )

    with patch(approve_patch) as mocked:
        mocked.return_value = (job_store.get(result.preflight_job_id), {"preflight_id": "rgf-test", "orchestration_job_id": "job-orch"})
        body, intent, meta = resolve_short_approval("approve", session_id="gf-approve")

    mocked.assert_called_once()
    assert mocked.call_args.args[0] == result.preflight_job_id
    assert intent == "pending_job_approval_resolved"
    assert result.preflight_job_id in body
    assert "Approval accepted for Railway greenfield deployment" in body


def test_correct_greenfield_approval_route_used(vault_paths, local_repo, monkeypatch):
    result = _run_greenfield_preflight(vault_paths, local_repo, monkeypatch, session_id="gf-route")
    target = get_session_approval_target("gf-route", result.preflight_job_id)
    assert target is not None
    assert target.approval_route == f"/api/v1/jobs/{result.preflight_job_id}/approve-railway-greenfield-preflight"


def test_multiple_pending_jobs_disambiguation(vault_paths, local_repo, monkeypatch):
    first = _run_greenfield_preflight(vault_paths, local_repo, monkeypatch, session_id="gf-multi")
    second = _run_greenfield_preflight(vault_paths, local_repo, monkeypatch, session_id="gf-multi")
    assert first.preflight_job_id != second.preflight_job_id

    body, intent, meta = resolve_short_approval("approve", session_id="gf-multi")
    assert intent == "pending_job_approval_disambiguation"
    assert first.preflight_job_id in body
    assert second.preflight_job_id in body
    assert meta.get("pending_count") == "2"


def test_expired_job_returns_blocker(vault_paths, local_repo, monkeypatch):
    result = _run_greenfield_preflight(vault_paths, local_repo, monkeypatch, session_id="gf-expired")
    target = get_session_approval_target("gf-expired", result.preflight_job_id)
    assert target is not None
    target.expires_at = (datetime.now(UTC) - timedelta(hours=1)).isoformat()

    body, intent, meta = resolve_short_approval("approve", session_id="gf-expired")
    assert intent == "pending_job_approval_blocked"
    assert meta.get("blocker") == "expired"
    assert "Approval could not be applied" in body


def test_no_pending_job_message():
    body, intent, meta = resolve_short_approval("approve", session_id="empty-session")
    assert intent == "pending_job_approval_none"
    assert "No active pending approval found" in body


def test_generic_job_approval_guidance_still_works_without_operational_context(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    job = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "atlas-trader api",
            "user_request": "Restart Railway atlas-trader api service",
        },
        source="test",
        session_id="generic-guidance",
        auto_run=False,
    )
    stored = job_store.get(job.id)
    stored.status = stored.status.__class__("completed")
    stored.params["preflight_status"] = "ready_for_mutation_approval"
    stored.params["mutation_preflight"] = {
        "provider": "railway",
        "operation_type": "restart",
        "target_name": "atlas-trader api",
        "preflight_status": "ready_for_mutation_approval",
    }

    reply = compose_job_approval_guidance_reply(f"where do i approve {job.id}?", session_id="generic-guidance")
    assert reply is not None
    assert "Approve it in" in reply
    get_settings.cache_clear()


def test_bare_approve_without_pending_does_not_hit_generic_guidance():
    body, intent, _meta = resolve_short_approval("approve", session_id="no-pending-guidance")
    assert intent == "pending_job_approval_none"
    assert "No active pending approval found" in body


def test_approval_response_does_not_expose_secrets(vault_paths, local_repo, monkeypatch):
    result = _run_greenfield_preflight(vault_paths, local_repo, monkeypatch, session_id="gf-secrets")
    chat = resolve_chat_turn("approve", session_id="gf-secrets", apply_relational_layer=False)
    assert _SECRET not in chat.reply


def test_chat_turn_resolves_greenfield_approve(vault_paths, local_repo, monkeypatch):
    _run_greenfield_preflight(vault_paths, local_repo, monkeypatch, session_id="gf-chat-approve")
    approve_patch = (
        "aethos_core.providers.railway.greenfield_deployment.greenfield_approval_flow."
        "approve_railway_greenfield_preflight"
    )

    with patch(approve_patch) as mocked:
        job = job_store.list_all()[0]
        mocked.return_value = (job, {"preflight_id": job.params.get("preflight_id"), "orchestration_job_id": "job-orch"})
        chat = resolve_chat_turn("approve", session_id="gf-chat-approve", apply_relational_layer=False)

    assert chat.intent == "pending_job_approval_resolved"
    assert "need more context" not in chat.reply.lower()
    assert "What specific action" not in chat.reply


def test_provider_e2e_orchestration_approval_route():
    job = authority.create_job(
        title="Railway E2E",
        job_type=PROVIDER_E2E_ORCHESTRATION_JOB_TYPE,
        params={
            "provider": "railway",
            "execution_status": "awaiting_approval",
            "provider_e2e_approved": False,
            "service_name": "aethos-api",
            "project_name": "aethos",
            "environment": "staging",
        },
        session_id="e2e-route",
        auto_run=False,
    )
    record_session_approval_target(
        session_id="e2e-route",
        job_id=job.id,
        job_type=PROVIDER_E2E_ORCHESTRATION_JOB_TYPE,
        provider="railway",
        action_type="provider_e2e_orchestration",
    )
    target = get_session_approval_target("e2e-route", job.id)
    assert target is not None
    assert target.approval_route == f"/api/v1/jobs/{job.id}/approve-provider-e2e-orchestration"
