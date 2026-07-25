# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow rerun live verification tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.github.mutations.workflow_rerun_verification import (
    summarize_verification_for_operator,
    update_correlation_after_rerun_verification,
)
from aethos_core.verification.github.workflow_rerun import verify_github_workflow_rerun


def test_verify_rerun_tracks_lineage_and_jobs(monkeypatch) -> None:
    monkeypatch.setattr("aethos_core.verification.github.workflow_rerun.time.sleep", lambda *_: None)
    runs = [
        {
            "id": 42,
            "workflow_id": 9,
            "run_number": 10,
            "created_at": "2026-01-01T00:00:00Z",
            "status": "completed",
            "conclusion": "failure",
            "head_branch": "main",
            "head_sha": "abc123",
            "name": "CI",
        },
        {
            "id": 99,
            "workflow_id": 9,
            "run_number": 11,
            "created_at": "2026-01-02T00:00:00Z",
            "status": "completed",
            "conclusion": "failure",
            "head_branch": "main",
            "head_sha": "abc123",
            "name": "CI",
        },
    ]

    def _fetch_runs(_token, *, repository, limit=20):
        return {"ok": True, "runs": runs}

    def _fetch_jobs(_token, *, owner, repo, run_id):
        return {
            "ok": True,
            "jobs": [
                {
                    "name": "build",
                    "conclusion": "failure",
                    "steps": [{"name": "npm test", "conclusion": "failure"}],
                }
            ],
        }

    monkeypatch.setattr("aethos_core.verification.github.workflow_rerun.fetch_workflow_runs", _fetch_runs)
    monkeypatch.setattr("aethos_core.verification.github.workflow_rerun.fetch_run_jobs", _fetch_jobs)

    result = verify_github_workflow_rerun(
        "token",
        repository="pilotmain/aethos",
        source_run_id=42,
        workflow_id=9,
        source_run_number=10,
        max_attempts=2,
        completion_poll_attempts=2,
        stabilization_wait_ms=0,
    )
    assert result["new_run_detected"] is True
    assert result["source_run_id"] == "42"
    assert result["rerun_run_id"] == 99
    assert result["rerun_outcome"] == "failed_again"
    assert result["likely_failure_job"] == "build"
    assert result["likely_failure_step"] == "npm test"


def test_update_correlation_persists_rerun_context() -> None:
    from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests, get_github_rerun_context

    clear_github_context_for_tests()
    update_correlation_after_rerun_verification(
        session_id="verify-session",
        repository="pilotmain/aethos",
        verification={
            "source_run_id": 42,
            "rerun_run_id": 99,
            "new_run_detected": True,
            "run_status": "completed",
            "run_conclusion": "failure",
            "run_number": 11,
            "head_branch": "main",
            "head_sha": "abc123",
            "workflow_name": "CI",
            "rerun_outcome": "failed_again",
            "likely_failure_job": "build",
            "likely_failure_step": "npm test",
            "deployment_chain": {"failure_boundary": "github", "chain_healthy": False},
            "chain_summary": "GitHub workflow rerun **failed again** — inspect failed jobs/steps on the rerun run.",
        },
    )
    ctx = get_github_rerun_context("verify-session")
    assert ctx is not None
    assert ctx["original_run_id"] == 42
    assert ctx["rerun_run_id"] == 99
    assert ctx["rerun_outcome"] == "failed_again"
    assert ctx["likely_failure_job"] == "build"


def test_summarize_includes_chain_not_workflow_only_success() -> None:
    text = summarize_verification_for_operator(
        {
            "rerun_outcome": "passed",
            "chain_summary": "GitHub workflow rerun **passed**, but the correlated Vercel deployment is still failing — workflow success is not deployment success.",
        }
    )
    assert "workflow success is not deployment success" in text
