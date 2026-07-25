# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.operations.mutations.execution import run_mutation_execution
from aethos_core.operations.mutations.failures import (
    PROVIDER_AUTH_FAILURE,
    RUN_NOT_DETECTED,
    classify_github_rerun_failure,
)
from aethos_core.operations.mutations.lifecycle import (
    EXECUTION_COMPLETED,
    VERIFICATION_PENDING,
)
from aethos_core.runtime.jobs import job_store
from aethos_core.verification.artifact import build_verification_artifact
from aethos_core.verification.github.workflow_rerun import verify_github_workflow_rerun
from aethos_core.verification.orchestration.resolve import resolve_mutation_verification


@pytest.fixture
def mutation_enabled(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_execution_completed_is_not_verified(mutation_enabled, monkeypatch):
    monkeypatch.setattr(
        "aethos_core.providers.railway.operations.mutation_adapter.RailwayMutationAdapter.execute",
        lambda self, *, operation, params: {"ok": True, "detail": "restarted", "operation": operation},
    )
    job_store._jobs.clear()
    job_store._events.clear()
    mutation = job_store.create(
        title="Mutation execution",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "mutation_execution_approved": True,
            "credential_id": "cred-1",
        },
        session_id="s962",
        auto_run=False,
    )
    outcome = run_mutation_execution(params=mutation.params, job_id=mutation.id)
    assert outcome.executed is True
    assert outcome.artifact["execution_state"] == EXECUTION_COMPLETED
    assert outcome.artifact["verification_state"] == VERIFICATION_PENDING
    assert outcome.artifact["verified"] is False
    assert "verification running" in outcome.summary.lower()


def test_classify_github_rerun_auth_failure():
    assert classify_github_rerun_failure(error_text="Bad credentials", http_status=401) == PROVIDER_AUTH_FAILURE


def test_verify_github_workflow_rerun_detects_new_run(monkeypatch):
    calls = {"n": 0}

    def fake_fetch(token, *, repository, limit=20):
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "ok": True,
                "runs": [
                    {"id": 99, "status": "in_progress", "run_number": 2},
                    {"id": 42, "status": "completed", "run_number": 1},
                ],
            }
        return {"ok": True, "runs": [{"id": 42, "status": "completed", "run_number": 1}]}

    monkeypatch.setattr(
        "aethos_core.verification.github.workflow_rerun.fetch_workflow_runs",
        fake_fetch,
    )
    monkeypatch.setattr("aethos_core.verification.github.workflow_rerun.time.sleep", lambda *_: None)

    result = verify_github_workflow_rerun("token", repository="owner/repo", source_run_id=42, max_attempts=2)
    assert result["ok"] is True
    assert result["new_run_id"] == 99
    assert result["verification_result"] in ("healthy", "pending")


def test_verify_github_workflow_rerun_run_not_detected(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.verification.github.workflow_rerun.fetch_workflow_runs",
        lambda token, *, repository, limit=20: {
            "ok": True,
            "runs": [{"id": 42, "status": "completed", "run_number": 1}],
        },
    )
    monkeypatch.setattr("aethos_core.verification.github.workflow_rerun.time.sleep", lambda *_: None)

    result = verify_github_workflow_rerun("token", repository="owner/repo", source_run_id=42, max_attempts=2)
    assert result["ok"] is False
    assert result["failure_type"] == RUN_NOT_DETECTED


def test_resolve_mutation_verification_updates_parent(monkeypatch):
    job_store._jobs.clear()
    job_store._events.clear()
    mutation = job_store.create(
        title="Mutation execution",
        job_type="mutation_execution",
        params={
            "provider": "github",
            "operation_type": "workflow_rerun",
            "target_name": "owner/aethos",
            "credential_id": "cred-gh",
            "executed": True,
            "execution_state": EXECUTION_COMPLETED,
            "verification_state": VERIFICATION_PENDING,
        },
        session_id="s962",
        auto_run=False,
    )
    verification = job_store.create(
        title="Post-mutation verification",
        job_type="readonly_execution",
        params={
            "provider": "github",
            "operation_type": "workflow_runs",
            "verification_of_mutation_job_id": mutation.id,
            "source_mutation_execution": {
                "provider": "github",
                "operation_type": "workflow_rerun",
                "provider_result": {"source_run_id": 42, "repository": "owner/aethos"},
            },
            "readonly_execution": {"summary": "runs listed"},
        },
        session_id="s962",
        auto_run=False,
    )
    job_store.complete_with_result(
        verification.id,
        full_result="ok",
        summary="ok",
        preview="ok",
        provider="readonly_execution",
        model="sandbox",
        used_llm=False,
        fallback=False,
    )

    monkeypatch.setattr(
        "aethos_core.providers.github.mutations.workflow_rerun_verification.verify_workflow_rerun",
        lambda token, *, repository, source_run_id, max_attempts=5, **kwargs: {
            "ok": True,
            "verification_result": "healthy",
            "new_run_id": 99,
            "new_run_detected": True,
            "rerun_outcome": "passed",
            "run_status": "completed",
            "run_conclusion": "success",
            "deployment_chain": {"chain_healthy": True, "failure_boundary": "none"},
            "retries": [{"retry_attempt": 2, "retry_reason": "provider_eventual_consistency", "retry_delay_ms": 2000}],
        },
    )
    monkeypatch.setattr(
        "aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token",
        lambda self, cid: "token",
    )

    artifact = resolve_mutation_verification(verification_job_id=verification.id)
    assert artifact is not None
    stored = job_store.get(mutation.id)
    assert stored.params["verification_state"] == "verified"
    assert stored.params["verified"] is True
    assert stored.params["lifecycle_state"] == "verified"
    assert stored.params.get("verification_retry_history")


def test_build_verification_artifact_shape():
    artifact = build_verification_artifact(
        provider="railway",
        operation="list_deployments",
        target="speakglobal-ai",
        linked_mutation_execution="job-xxxx",
        verification_result="healthy",
    )
    assert artifact["verification_type"] == "readonly_verification"
    assert artifact["linked_mutation_execution"] == "job-xxxx"
    assert artifact["verification_result"] == "healthy"


def test_github_rerun_returns_pending_verification_on_http_success(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.providers.github.operations.mutations_api.resolve_repository",
        lambda token, repository: {"ok": True, "full_name": "owner/aethos", "owner": "owner", "repo": "aethos"},
    )
    monkeypatch.setattr(
        "aethos_core.providers.github.operations.mutations_api.resolve_latest_workflow_run",
        lambda token, repository, limit=20, workflow_id=None, workflow_name=None: {
            "ok": True,
            "repository": repository,
            "workflow_id": "wf-1",
            "source_run_id": 42,
            "run": {"id": 42, "workflow_id": "wf-1", "run_number": 1, "status": "completed"},
        },
    )
    monkeypatch.setattr(
        "aethos_core.providers.github.operations.mutations_api.request_github",
        lambda token, method, path, **kwargs: {"ok": True, "data": {}, "http_status": 201},
    )
    from aethos_core.providers.github.operations.mutations_api import rerun_latest_workflow

    result = rerun_latest_workflow("token", repository="owner/aethos")
    assert result["ok"] is True
    assert result["rerun_attempted"] is True
    assert result["verification_result"] == "pending"
    assert result["http_status"] == 201
