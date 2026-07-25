# SPDX-License-Identifier: Apache-2.0
"""FUNCTIONALITY_REALITY_SPRINT_002 — provider E2E orchestration executor tests."""

from __future__ import annotations

import pytest

from aethos_core.provider_e2e_execution.job_taxonomy import PROVIDER_E2E_ORCHESTRATION_JOB_TYPE
from aethos_core.provider_e2e_orchestration.approval_flow import approve_provider_e2e_orchestration
from aethos_core.provider_e2e_orchestration.approval_gate import ProviderE2EApprovalError, validate_approval_gate
from aethos_core.provider_e2e_orchestration.executor import run_provider_e2e_orchestration
from aethos_core.provider_e2e_orchestration.final_report import compose_provider_e2e_final_report
from aethos_core.provider_e2e_orchestration.job_model import enrich_job_params_for_orchestration
from aethos_core.runtime.authority import authority
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _isolate_jobs():
    job_store.clear_for_tests()
    job_executor.drain_queue_for_tests()
    yield
    job_store.clear_for_tests()
    job_executor.drain_queue_for_tests()


def _railway_job_params(**extra):
    base = enrich_job_params_for_orchestration(
        {
            "provider": "railway",
            "target": {"project_name": "aethos", "environment_name": "production", "service_name": "aethos-api"},
            "service_name": "aethos-api",
            "project_name": "aethos",
            "environment": "production",
            "env_var_names": ["ANTHROPIC_API_KEY"],
            "_test_env_values": {"ANTHROPIC_API_KEY": "test-secret-value-never-logged"},
        }
    )
    base.update(extra)
    return base


def _create_orchestration_job(**params):
    return authority.create_job(
        title="Railway E2E test",
        job_type=PROVIDER_E2E_ORCHESTRATION_JOB_TYPE,
        params=params,
        session_id="sprint-002",
        auto_run=False,
    )


def test_missing_approval_blocks_execution():
    job = _create_orchestration_job(**_railway_job_params())
    outcome = run_provider_e2e_orchestration(job_id=job.id, params=job.params)
    assert outcome.blocked is True
    assert outcome.executed is False
    assert outcome.artifact.get("failure_state") == "missing_approval"


def test_mutation_execution_disabled_blocks_approval(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        lambda: ("token", "test", None),
    )
    job = _create_orchestration_job(**_railway_job_params())
    gate = validate_approval_gate(job)
    assert gate.ok is False
    assert gate.failure_state == "mutation_execution_disabled"
    with pytest.raises(ProviderE2EApprovalError):
        approve_provider_e2e_orchestration(job.id)
    get_settings.cache_clear()


def test_production_gate_blocks_approval(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        lambda: ("token", "test", None),
    )
    job = _create_orchestration_job(**_railway_job_params(environment="production"))
    gate = validate_approval_gate(job)
    assert gate.ok is False
    assert gate.failure_state == "production_gate_required"
    get_settings.cache_clear()


def test_railway_approved_executor_chain(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "true")
    monkeypatch.setenv("PROVIDER_ENV_VAR_MUTATIONS_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    monkeypatch.setattr(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        lambda: ("token", "test", None),
    )
    monkeypatch.setattr(
        "aethos_core.provider_e2e_orchestration.executor.apply_env_vars",
        lambda *a, **k: {"ok": True, "applied_names": ["ANTHROPIC_API_KEY"], "failed_names": [], "detail": "test"},
    )
    monkeypatch.setattr(
        "aethos_core.provider_e2e_orchestration.executor.execute_redeploy",
        lambda *a, **k: {"ok": True, "deployment_id": "dep-123", "detail": "redeploy ok"},
    )
    monkeypatch.setattr(
        "aethos_core.provider_e2e_orchestration.executor.poll_deployment_status",
        lambda *a, **k: {
            "ok": True,
            "final_state": "ready",
            "deployment_id": "dep-123",
            "deployment_url": "https://aethos-api.up.railway.app",
            "timeline": [{"mapped_state": "ready"}],
        },
    )
    monkeypatch.setattr(
        "aethos_core.provider_e2e_orchestration.executor.verify_health",
        lambda *a, **k: {"ok": True, "url": "https://aethos-api.up.railway.app", "status_code": 200},
    )

    job = _create_orchestration_job(**_railway_job_params())
    approve_provider_e2e_orchestration(job.id)
    assert job_executor.drain_once_for_tests() is True

    finished = job_store.get(job.id)
    assert finished is not None
    assert finished.status.value == "completed"
    assert finished.params.get("execution_status") == "completed"
    report = finished.params.get("provider_e2e_final_report") or {}
    full = str(report.get("full_report") or finished.full_result or "")
    assert "test-secret-value" not in full
    assert "***" not in full or "ANTHROPIC_API_KEY" in full
    assert "dep-123" in full or "dep-123" in str(finished.params.get("provider_e2e_evidence_bundle") or "")


def test_env_failure_stops_deploy(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        lambda: ("token", "test", None),
    )
    monkeypatch.setattr(
        "aethos_core.provider_e2e_orchestration.executor.apply_env_vars",
        lambda *a, **k: {"ok": False, "applied_names": [], "failed_names": ["ANTHROPIC_API_KEY"], "detail": "fail"},
    )
    redeploy_called = {"n": 0}

    def _redeploy(*a, **k):
        redeploy_called["n"] += 1
        return {"ok": True}

    monkeypatch.setattr("aethos_core.provider_e2e_orchestration.executor.execute_redeploy", _redeploy)

    params = _railway_job_params(provider_e2e_approved=True, approval_id="test-approval")
    job = _create_orchestration_job(**params)
    outcome = run_provider_e2e_orchestration(job_id=job.id, params=job.params)
    assert outcome.artifact.get("execution_status") == "env_failed"
    assert redeploy_called["n"] == 0


def test_vercel_executor_final_report_url(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    params = enrich_job_params_for_orchestration(
        {
            "provider": "vercel",
            "project_name": "aethos-web",
            "target": {"project_name": "aethos-web"},
            "credential_id": "cred-vercel",
            "env_var_names": [],
            "provider_e2e_approved": True,
            "approval_id": "apr-1",
        }
    )
    monkeypatch.setattr(
        "aethos_core.providers.vercel.auth.VercelAuthAdapter.resolve_best_auth_method",
        lambda self, **k: {"method": "api_token", "credential_id": "cred-vercel"},
    )
    monkeypatch.setattr(
        "aethos_core.providers.vercel.auth.VercelAuthAdapter.get_api_token",
        lambda self, cid: "vercel-test-token",
    )
    monkeypatch.setattr(
        "aethos_core.provider_e2e_orchestration.executor.apply_env_vars",
        lambda *a, **k: {"ok": True, "skipped": True, "applied_names": [], "failed_names": []},
    )
    monkeypatch.setattr(
        "aethos_core.provider_e2e_orchestration.executor.execute_redeploy",
        lambda *a, **k: {"ok": True, "deployment_id": "dpl_vercel_1", "detail": "ok"},
    )
    monkeypatch.setattr(
        "aethos_core.provider_e2e_orchestration.executor.poll_deployment_status",
        lambda *a, **k: {
            "ok": True,
            "final_state": "ready",
            "deployment_url": "https://aethos.vercel.app",
            "timeline": [],
        },
    )
    monkeypatch.setattr(
        "aethos_core.provider_e2e_orchestration.executor.verify_health",
        lambda *a, **k: {"ok": True, "url": "https://aethos.vercel.app", "status_code": 200},
    )
    job = _create_orchestration_job(**params)
    outcome = run_provider_e2e_orchestration(job_id=job.id, params=job.params)
    assert outcome.executed is True
    evidence = outcome.artifact.get("provider_e2e_evidence_bundle") or {}
    report = compose_provider_e2e_final_report(
        provider="vercel", evidence=evidence, execution_status="completed"
    )
    assert "aethos.vercel.app" in report
    assert "vercel-test-token" not in report


def test_final_report_always_generated_on_redeploy_failure(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        lambda: ("token", "test", None),
    )
    monkeypatch.setattr(
        "aethos_core.provider_e2e_orchestration.executor.apply_env_vars",
        lambda *a, **k: {"ok": True, "skipped": True, "applied_names": [], "failed_names": []},
    )
    monkeypatch.setattr(
        "aethos_core.provider_e2e_orchestration.executor.execute_redeploy",
        lambda *a, **k: {"ok": False, "detail": "redeploy failed"},
    )
    params = _railway_job_params(provider_e2e_approved=True, approval_id="apr-2", env_var_names=[])
    job = _create_orchestration_job(**params)
    outcome = run_provider_e2e_orchestration(job_id=job.id, params=job.params)
    assert outcome.full_result
    assert outcome.artifact.get("provider_e2e_final_report")
