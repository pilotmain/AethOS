# SPDX-License-Identifier: Apache-2.0
"""Phase 9.6.3 lifecycle authority and GitHub verification hardening."""

from __future__ import annotations

import pytest

from aethos_core.operations.mutations.lifecycle_authority import (
    AUDIT_RECORDED,
    VERIFICATION_RUNNING_STATE,
    canonical_mutation_state,
    mutation_summary,
    sync_mutation_job_lifecycle,
)
from aethos_core.runtime.jobs import job_store
from aethos_core.verification.github.workflow_rerun import verify_github_workflow_rerun
from aethos_core.verification.orchestration.resolve import resolve_mutation_verification


def test_lifecycle_summary_sync_after_verification(monkeypatch):
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
            "execution_state": "execution_completed",
            "verification_state": "verification_pending",
            "verification_job_id": "verify-1",
        },
        session_id="s963",
        auto_run=False,
    )
    verification = job_store.create(
        title="Verify",
        job_type="readonly_execution",
        params={
            "provider": "github",
            "operation_type": "workflow_runs",
            "verification_of_mutation_job_id": mutation.id,
            "source_mutation_execution": {
                "provider": "github",
                "operation_type": "workflow_rerun",
                "provider_result": {
                    "source_run_id": 42,
                    "workflow_id": 99,
                    "repository": "owner/aethos",
                    "source_created_at": "2026-01-01T00:00:00Z",
                    "source_run_number": 1,
                },
            },
            "readonly_execution": {"summary": "runs ok"},
        },
        session_id="s963",
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
        lambda *a, **k: {
            "ok": True,
            "verification_result": "healthy",
            "new_run_id": 100,
            "new_run_detected": True,
            "rerun_outcome": "passed",
            "run_status": "completed",
            "run_conclusion": "success",
            "deployment_chain": {"chain_healthy": True, "failure_boundary": "none"},
            "verification_attempts": 2,
            "retries": [],
        },
    )
    monkeypatch.setattr(
        "aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token",
        lambda self, cid: "token",
    )

    resolve_mutation_verification(verification_job_id=verification.id)
    stored = job_store.get(mutation.id)
    assert stored.params["verified"] is True
    assert stored.params["verification_state"] == "verified"
    assert "verified healthy" in stored.result_summary
    assert stored.params.get("lifecycle_summary") == stored.result_summary
    assert canonical_mutation_state(stored.params) in (AUDIT_RECORDED, "verified")


def test_github_verification_uses_stabilization_wait(monkeypatch):
    sleeps: list[float] = []

    def fake_sleep(sec: float) -> None:
        sleeps.append(sec)

    monkeypatch.setattr("aethos_core.verification.github.workflow_rerun.time.sleep", fake_sleep)
    monkeypatch.setattr(
        "aethos_core.verification.github.workflow_rerun.fetch_workflow_runs",
        lambda *a, **k: {
            "ok": True,
            "runs": [{"id": 100, "workflow_id": 99, "status": "queued", "created_at": "2026-01-02T00:00:00Z", "run_number": 2}],
        },
    )

    result = verify_github_workflow_rerun(
        "token",
        repository="owner/aethos",
        source_run_id=42,
        workflow_id=99,
        source_created_at="2026-01-01T00:00:00Z",
        source_run_number=1,
        stabilization_wait_ms=4000,
        max_attempts=1,
    )
    assert result["ok"] is True
    assert result["new_run_detected"] is True
    assert sleeps and sleeps[0] == 4.0


def test_mutation_summary_verification_running():
    text = mutation_summary(
        provider="railway",
        operation_type="restart",
        target="speakglobal-ai",
        canonical_state=VERIFICATION_RUNNING_STATE,
    )
    assert "verification running" in text
    assert "verification pending" not in text or "execution completed" in text
