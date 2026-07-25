# SPDX-License-Identifier: Apache-2.0
"""Tests for AETHOS_SOLO_PRODUCTION_EXECUTION_MODE."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.connections.validation_status import VALIDATED
from aethos_core.jobs.pending_job_approval_resolution import resolve_short_approval
from aethos_core.jobs.session_approval_target import clear_session_approval_targets_for_tests
from aethos_core.providers.railway.execution_contract.execution_journal import clear_for_tests as clear_execution_journals
from aethos_core.providers.railway.greenfield_deployment.greenfield_flow import run_railway_greenfield_deployment_flow
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store
from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests
from aethos_core.solo_execution.solo_execution_mode import validate_solo_greenfield_eligibility
from aethos_core.solo_execution.solo_final_report import compose_solo_greenfield_final_report

_SECRET = "railway_solo_secret_token_1234567890"
_LIST_SERVICES_PATCH = "aethos_core.providers.railway.credential_truth.list_services_with_status"
_ENV_RESOLVE_PATCH = "aethos_core.providers.railway.env_value_readiness.env_secure_resolution.resolve_env_var_from_secure_store"
_PHASE_PATCH = "aethos_core.solo_execution.solo_greenfield_executor.run_single_real_mutation_phase"

GREENFIELD_PROMPT = (
    "AethOS is a new project. Check local workspace, get its remote git, "
    "create a new Railway project, deploy, set required env vars, and report back."
)


@pytest.fixture(autouse=True)
def _isolate():
    job_store.clear_for_tests()
    job_executor.drain_queue_for_tests()
    clear_session_approval_targets_for_tests()
    clear_execution_journals()
    yield
    job_store.clear_for_tests()
    job_executor.drain_queue_for_tests()
    clear_session_approval_targets_for_tests()
    clear_execution_journals()


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


def _env_ok(name, plan=None):
    _ = plan
    from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import SecureEnvResolution

    return SecureEnvResolution(name=str(name), ok=True, value="resolved", source="credential_center")


def _env_missing(name, plan=None):
    _ = plan
    from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import SecureEnvResolution

    return SecureEnvResolution(name=str(name), ok=False, blocked_reason="missing")


def _enable_solo(monkeypatch):
    monkeypatch.setenv("AETHOS_SOLO_EXECUTION_MODE", "true")
    monkeypatch.setenv("AETHOS_SOLO_EXECUTION_PROVIDER", "railway")
    monkeypatch.setenv("AETHOS_SOLO_AUTO_APPROVE", "true")
    monkeypatch.setenv("AETHOS_SOLO_AUTO_APPROVE_PHASES", "true")
    monkeypatch.setenv("AETHOS_LOCAL_ENV_TRUSTED", "true")
    monkeypatch.setenv("AETHOS_SOLO_REQUIRE_FINAL_CONFIRMATION", "false")
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("AETHOS_SOLO_ALLOWED_REPOS", "pilotmain/AethOS")
    monkeypatch.setenv("AETHOS_SOLO_ALLOWED_PROVIDERS", "railway")
    monkeypatch.setenv("AETHOS_SOLO_ALLOWED_ENVIRONMENTS", "staging")
    monkeypatch.setenv("AETHOS_SOLO_ALLOW_PRODUCTION", "false")
    get_settings.cache_clear()


def _run_flow(vault_paths, local_repo, monkeypatch, session_id: str, *, solo: bool = False):
    _store_validated(vault_paths)
    if solo:
        _enable_solo(monkeypatch)
    else:
        monkeypatch.setenv("AETHOS_SOLO_EXECUTION_MODE", "false")
        get_settings.cache_clear()
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.local_workspace_source.resolve_configured_workspace_root",
        lambda: local_repo,
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        lambda: ("token", "test", None),
    )
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok), patch(_ENV_RESOLVE_PATCH, side_effect=_env_ok):
        return run_railway_greenfield_deployment_flow(GREENFIELD_PROMPT, session_id=session_id)


def test_solo_mode_disabled_preserves_approval_requirement(vault_paths, local_repo, monkeypatch):
    result = _run_flow(vault_paths, local_repo, monkeypatch, "solo-off", solo=False)
    assert result.intent == "railway_greenfield_deployment_preflight"
    assert "Approval: **required**" in result.reply
    assert result.artifacts.get("solo_execution") is not True


def test_solo_mode_enabled_auto_executes_allowlisted_staging(vault_paths, local_repo, monkeypatch):
    _enable_solo(monkeypatch)

    class _PhaseResult:
        def __init__(self, journal):
            self.journal = journal
            self.policy_blocked = False
            self.errors = []
            self.idempotent_replay = True
            self.detail = "done"

    def _phase(journal, plan, policy, user_text=""):
        _ = (plan, policy, user_text)
        updated = dict(journal)
        updated["railway_service_id"] = "svc-solo"
        updated["railway_deployment_id"] = "dep-solo"
        updated["deployment_url"] = "https://aethos-api.up.railway.app"
        updated["runtime_verification_performed"] = True
        updated["runtime_verification"] = {"ok": True, "verified": True, "status_code": 200}
        return _PhaseResult(updated)

    with patch(_PHASE_PATCH, side_effect=_phase):
        result = _run_flow(vault_paths, local_repo, monkeypatch, "solo-on", solo=True)

    assert result.intent == "railway_greenfield_solo_execution_completed"
    assert "Railway deploy complete" in result.reply
    assert "aethos-api" in result.reply
    assert _SECRET not in result.reply


def test_non_allowlisted_repo_blocked(vault_paths, local_repo, monkeypatch):
    _enable_solo(monkeypatch)
    subprocess.run(
        ["git", "remote", "set-url", "origin", "git@github.com:other/Repo.git"],
        cwd=local_repo,
        check=True,
        capture_output=True,
    )
    from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import (
        resolve_git_remote_from_workspace,
    )

    git_remote = resolve_git_remote_from_workspace(local_repo)
    result = validate_solo_greenfield_eligibility(
        plan={
            "repo": "pilotmain/AethOS",
            "environment": "staging",
            "project": "pilotos",
            "service_name": "aethos-api",
        },
        env_report={"required_env_var_names": ["ANTHROPIC_API_KEY"]},
        git_remote=git_remote,
        provider="railway",
    )
    assert result.ok is False
    assert result.blocker_code == "SOLO_REPO_NOT_ALLOWED"


def test_production_target_blocked_unless_flag(monkeypatch):
    _enable_solo(monkeypatch)
    eligibility = validate_solo_greenfield_eligibility(
        plan={
            "repo": "pilotmain/AethOS",
            "environment": "production",
            "project": "pilotos",
            "service_name": "aethos-api",
        },
        env_report={"required_env_var_names": ["ANTHROPIC_API_KEY"]},
        git_remote={"repository": "pilotmain/AethOS"},
        provider="railway",
    )
    assert eligibility.ok is False
    assert eligibility.blocker_code == "SOLO_PRODUCTION_NOT_ALLOWED"


def test_secret_values_never_appear_in_solo_output(vault_paths, local_repo, monkeypatch):
    _enable_solo(monkeypatch)

    def _phase(journal, plan, policy, user_text=""):
        _ = (plan, policy, user_text)
        updated = dict(journal)
        updated["railway_deployment_id"] = "dep-solo"
        updated["runtime_verification_performed"] = True

        class _PhaseResult:
            pass

        result = _PhaseResult()
        result.journal = updated
        result.policy_blocked = False
        result.errors = []
        result.idempotent_replay = True
        result.detail = "done"
        return result

    with patch(_PHASE_PATCH, side_effect=_phase):
        chat = resolve_chat_turn(GREENFIELD_PROMPT, session_id="solo-secrets", apply_relational_layer=False)

    assert _SECRET not in chat.reply


def test_greenfield_flow_continues_after_target_service_missing(vault_paths, local_repo, monkeypatch):
    _enable_solo(monkeypatch)

    def _phase(journal, plan, policy, user_text=""):
        _ = (plan, policy, user_text)

        class _PhaseResult:
            pass

        result = _PhaseResult()
        result.journal = dict(journal)
        result.journal["railway_deployment_id"] = "dep-continue"
        result.journal["runtime_verification_performed"] = True
        result.journal["runtime_verification"] = {"verified": True, "ok": True}
        result.policy_blocked = False
        result.errors = []
        result.idempotent_replay = True
        result.detail = "done"
        return result

    with patch(_PHASE_PATCH, side_effect=_phase):
        result = _run_flow(vault_paths, local_repo, monkeypatch, "solo-continue", solo=True)

    assert "TARGET_SERVICE_MISSING" not in result.reply
    assert "Railway deploy complete" in result.reply


def test_final_report_generated_on_success():
    report = compose_solo_greenfield_final_report(
        plan={"project": "pilotos", "service_name": "aethos-api", "environment": "staging", "repo": "pilotmain/AethOS", "branch": "main"},
        git_remote={"repository": "pilotmain/AethOS", "branch": "main"},
        journal={
            "railway_deployment_id": "dep-1",
            "deployment_url": "https://aethos-api.up.railway.app",
            "runtime_verification": {"ok": True, "status_code": 200},
            "runtime_verification_performed": True,
        },
        env_report={"required_env_var_names": ["ANTHROPIC_API_KEY"]},
        preflight_id="rgf-test",
        preflight_job_id="job-test",
        execution_status="completed",
    )
    assert "dep-1" in report
    assert "ANTHROPIC_API_KEY" in report
    assert "secret" not in report.lower() or "No secret values" in report


def test_missing_env_reference_blocker(vault_paths, local_repo, monkeypatch):
    _enable_solo(monkeypatch)
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.local_workspace_source.resolve_configured_workspace_root",
        lambda: local_repo,
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        lambda: ("token", "test", None),
    )
    _store_validated(vault_paths)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok), patch(_ENV_RESOLVE_PATCH, side_effect=_env_missing):
        result = run_railway_greenfield_deployment_flow(GREENFIELD_PROMPT, session_id="solo-env-missing")

    assert result.blocked is True
    assert result.blocker_code == "SOLO_MISSING_ENV_REFERENCE"


def test_destructive_actions_blocked(monkeypatch):
    _enable_solo(monkeypatch)
    eligibility = validate_solo_greenfield_eligibility(
        plan={"repo": "pilotmain/AethOS", "environment": "staging", "project": "pilotos", "service_name": "aethos-api"},
        env_report={"required_env_var_names": []},
        git_remote={"repository": "pilotmain/AethOS"},
        provider="railway",
        user_text="delete database on railway",
    )
    assert eligibility.ok is False
    assert eligibility.blocker_code == "SOLO_DESTRUCTIVE_ACTION_BLOCKED"


def test_existing_mission_control_approval_still_works_without_solo(vault_paths, local_repo, monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "true")
    monkeypatch.setenv("PROVIDER_ENV_VAR_MUTATIONS_ENABLED", "true")
    get_settings.cache_clear()
    result = _run_flow(vault_paths, local_repo, monkeypatch, "solo-approval-path", solo=False)
    assert result.preflight_job_id
    approve_patch = (
        "aethos_core.providers.railway.greenfield_deployment.greenfield_approval_flow."
        "approve_railway_greenfield_preflight"
    )
    with patch(approve_patch) as mocked:
        job = job_store.get(result.preflight_job_id)
        mocked.return_value = (job, {"preflight_id": "rgf-test", "orchestration_job_id": "job-orch"})
        body, intent, _meta = resolve_short_approval("approve", session_id="solo-approval-path")
    assert intent == "pending_job_approval_resolved"
    assert "Approval accepted" in body
