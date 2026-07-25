# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow rerun outcome classification tests."""

from __future__ import annotations

from aethos_core.providers.github.mutations.workflow_rerun_outcome import (
    analyze_rerun_deployment_chain,
    chain_verification_result,
    classify_rerun_outcome,
    summarize_failed_jobs,
)


def test_classify_rerun_outcome_passed() -> None:
    assert classify_rerun_outcome(new_run_detected=True, run_status="completed", run_conclusion="success") == "passed"


def test_classify_rerun_outcome_failed_again() -> None:
    assert classify_rerun_outcome(new_run_detected=True, run_status="completed", run_conclusion="failure") == "failed_again"


def test_classify_rerun_outcome_cancelled() -> None:
    assert classify_rerun_outcome(new_run_detected=True, run_status="completed", run_conclusion="cancelled") == "cancelled"


def test_classify_rerun_outcome_timed_out() -> None:
    assert (
        classify_rerun_outcome(
            new_run_detected=True,
            run_status="in_progress",
            run_conclusion="",
            completion_timed_out=True,
        )
        == "timed_out"
    )


def test_classify_rerun_outcome_not_detected() -> None:
    assert classify_rerun_outcome(new_run_detected=False) == "rerun_not_detected"


def test_summarize_failed_jobs() -> None:
    summary = summarize_failed_jobs(
        [
            {
                "name": "build",
                "conclusion": "failure",
                "steps": [{"name": "npm test", "conclusion": "failure"}],
            }
        ]
    )
    assert summary["likely_failure_job"] == "build"
    assert summary["likely_failure_step"] == "npm test"
    assert summary["failed_job_count"] == 1


def test_chain_verification_workflow_passed_deploy_failed() -> None:
    chain = {
        "chain_healthy": False,
        "workflow_passed_deploy_failed": True,
        "failure_boundary": "vercel",
    }
    assert chain_verification_result(rerun_outcome="passed", deployment_chain=chain) == "inconclusive"


def test_chain_verification_full_chain_healthy() -> None:
    chain = {"chain_healthy": True, "failure_boundary": "none"}
    assert chain_verification_result(rerun_outcome="passed", deployment_chain=chain) == "healthy"


def test_analyze_chain_detects_workflow_passed_deploy_failed() -> None:
    from aethos_core.cross_provider_correlation.correlation_store import clear_store_for_tests, publish_github_evidence, publish_vercel_evidence

    clear_store_for_tests()
    publish_github_evidence(
        "chain-test",
        {
            "repository": "pilotmain/aethos",
            "branch": {"branch": "main"},
            "commits": {"commits": [{"sha": "abc123", "message": "fix", "author": "raya"}]},
            "checks": {"ok": True, "failed_count": 0, "checks": []},
            "workflow_diagnostic": {"ok": True, "latest_failed_run": None},
            "workflow_runs": {"ok": True, "runs": []},
        },
    )
    publish_vercel_evidence(
        "chain-test",
        {
            "project_name": "aethos-web",
            "project": {"details": {"repo_link": "pilotmain/aethos"}},
            "latest_deployment": {"id": "d1", "state": "error", "commit": "abc123"},
            "failed_deployment": {"id": "d1", "state": "error", "commit": "abc123"},
            "build_analysis": {"error_lines": ["build failed"]},
        },
    )
    from aethos_core.cross_provider_correlation.evidence_publisher import ingest_github_live_evidence, ingest_vercel_live_evidence

    ingest_github_live_evidence(
        "chain-test",
        {
            "repository": "pilotmain/aethos",
            "branch": {"branch": "main"},
            "commits": {"commits": [{"sha": "abc123", "message": "fix", "author": "raya"}]},
            "checks": {"ok": True, "failed_count": 0, "checks": []},
            "workflow_diagnostic": {"ok": True, "latest_failed_run": None},
            "workflow_runs": {"ok": True, "runs": []},
        },
    )
    ingest_vercel_live_evidence(
        "chain-test",
        {
            "project_name": "aethos-web",
            "project": {"details": {"repo_link": "pilotmain/aethos"}},
            "latest_deployment": {"id": "d1", "state": "error", "commit": "abc123"},
            "failed_deployment": {"id": "d1", "state": "error", "commit": "abc123"},
            "build_analysis": {"error_lines": ["build failed"]},
        },
    )
    chain = analyze_rerun_deployment_chain(session_id="chain-test", rerun_outcome="passed")
    assert chain["workflow_passed_deploy_failed"] is True
    assert chain["failure_boundary"] == "vercel"
