# SPDX-License-Identifier: Apache-2.0
"""Post-rerun downstream evidence refresh tests."""

from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import patch

from aethos_core.cross_provider_correlation.correlation_store import (
    clear_store_for_tests,
    publish_github_evidence,
    publish_railway_evidence,
    publish_vercel_evidence,
)
from aethos_core.providers.github.context.github_context_store import (
    clear_github_context_for_tests,
    get_github_rerun_context,
)
from aethos_core.providers.github.mutations.post_rerun_evidence_refresh import (
    _analyze_deployments_for_rerun,
    _build_rerun_timeline,
    _classify_chain_verdict,
    refresh_downstream_evidence_after_rerun,
)
from aethos_core.providers.github.mutations.post_rerun_poll_config import PostRerunPollConfig
from aethos_core.providers.github.mutations.rerun_followup_router import compose_github_workflow_rerun_followup_reply
from aethos_core.providers.github.mutations.workflow_rerun_verification import (
    update_correlation_after_rerun_verification,
)


def setup_function() -> None:
    clear_store_for_tests()
    clear_github_context_for_tests()


def _seed_github_vercel_railway(
    session_id: str,
    *,
    github_status: str = "passed",
    vercel_state: str = "ready",
    vercel_deploy_id: str = "d-old",
    railway_status: str = "healthy",
    commit: str = "abc123def456",
) -> None:
    publish_github_evidence(
        session_id,
        {
            "repository": "pilotmain/aethos",
            "branch": {"branch": "main", "sha": commit},
            "commits": {"commits": [{"sha": commit, "message": "fix", "author": "raya"}]},
            "checks": {"ok": github_status == "passed", "failed_count": 0 if github_status == "passed" else 1, "checks": []},
            "workflow_diagnostic": {"ok": True, "latest_failed_run": None},
            "workflow_runs": {"ok": True, "runs": []},
        },
    )
    publish_vercel_evidence(
        session_id,
        {
            "project_name": "aethos-web",
            "project": {"details": {"repo_link": "pilotmain/aethos", "name": "aethos-web"}},
            "latest_deployment": {"id": vercel_deploy_id, "state": vercel_state, "commit": commit, "branch": "main"},
            "failed_deployment": {"id": vercel_deploy_id, "state": vercel_state, "commit": commit, "branch": "main"}
            if vercel_state in {"error", "failed"}
            else None,
        },
    )
    publish_railway_evidence(
        session_id,
        {
            "project": "aethos",
            "service": "aethos-api",
            "status": railway_status,
            "commit_sha": commit,
        },
    )


def _poll_patches(*, fetch_return: dict, vercel_payload: dict | None = None):
    stack = ExitStack()
    stack.enter_context(
        patch(
            "aethos_core.providers.github.mutations.post_rerun_evidence_refresh._resolve_vercel_token",
            return_value="vercel-token",
        )
    )
    stack.enter_context(
        patch(
            "aethos_core.providers.vercel.operations.deployments_api.fetch_deployments",
            return_value=fetch_return,
        )
    )
    stack.enter_context(
        patch(
            "aethos_core.providers.vercel.diagnostics.deployment_evidence_collector.collect_vercel_live_evidence",
            return_value=vercel_payload or fetch_return,
        )
    )
    stack.enter_context(
        patch(
            "aethos_core.providers.github.mutations.post_rerun_evidence_refresh._sleep_seconds",
        )
    )
    stack.enter_context(
        patch(
            "aethos_core.providers.github.mutations.post_rerun_evidence_refresh.PostRerunPollConfig.from_env",
            return_value=PostRerunPollConfig(deploy_poll_seconds=10, deploy_poll_interval_seconds=1, runtime_settle_seconds=0),
        )
    )
    stack.enter_context(
        patch(
            "aethos_core.cross_provider_correlation.correlation_store.publish_railway_health_rows",
            return_value=True,
        )
    )
    return stack


def test_refresh_detects_new_deployment_for_rerun_commit() -> None:
    _seed_github_vercel_railway("refresh-new", vercel_deploy_id="d-old")
    vercel_payload = {
        "ok": True,
        "project_name": "aethos-web",
        "deployments": {
            "deployments": [
                {"id": "d-new", "state": "ready", "commit": "abc123def456", "branch": "main", "created_at": "2026-01-03"},
                {"id": "d-old", "state": "ready", "commit": "abc123def456", "branch": "main", "created_at": "2026-01-01"},
            ]
        },
        "latest_deployment": {"id": "d-new", "state": "ready", "commit": "abc123def456", "branch": "main"},
        "project": {"details": {"repo_link": "pilotmain/aethos", "name": "aethos-web"}},
    }
    fetch_return = {
        "ok": True,
        "deployments": [
            {"id": "d-new", "state": "ready", "commit": "abc123def456", "branch": "main", "created_at": "2026-01-03"},
            {"id": "d-old", "state": "ready", "commit": "abc123def456", "branch": "main", "created_at": "2026-01-01"},
        ],
    }
    with _poll_patches(fetch_return=fetch_return, vercel_payload=vercel_payload):
        result = refresh_downstream_evidence_after_rerun(
            session_id="refresh-new",
            repository="pilotmain/aethos",
            verification={
                "rerun_outcome": "passed",
                "head_sha": "abc123def456",
                "run_status": "completed",
                "run_conclusion": "success",
                "run_number": 12,
                "rerun_run_id": 100,
            },
        )
    chain = result["deployment_chain"]
    assert result["evidence_refreshed"] is True
    assert chain["new_deployment_created"] is True
    assert chain["chain_verdict"] == "chain_healthy"
    assert any(event["phase"] == "deploy_observed" for event in chain["timeline"])


def test_refresh_detects_deploy_not_triggered() -> None:
    _seed_github_vercel_railway("refresh-no-deploy", vercel_deploy_id="d-old", commit="oldcommit111")
    vercel_payload = {
        "ok": True,
        "project_name": "aethos-web",
        "deployments": {
            "deployments": [
                {"id": "d-old", "state": "ready", "commit": "oldcommit111", "branch": "main"},
            ]
        },
        "latest_deployment": {"id": "d-old", "state": "ready", "commit": "oldcommit111", "branch": "main"},
        "project": {"details": {"repo_link": "pilotmain/aethos", "name": "aethos-web"}},
    }
    fetch_return = {"ok": True, "deployments": [{"id": "d-old", "state": "ready", "commit": "oldcommit111", "branch": "main"}]}
    with _poll_patches(fetch_return=fetch_return, vercel_payload=vercel_payload):
        result = refresh_downstream_evidence_after_rerun(
            session_id="refresh-no-deploy",
            repository="pilotmain/aethos",
            verification={
                "rerun_outcome": "passed",
                "head_sha": "newcommit222",
                "run_status": "completed",
                "run_conclusion": "success",
            },
        )
    assert result["chain_verdict"] == "deploy_not_triggered_after_wait"
    assert result["deployment_chain"]["no_deploy_triggered"] is True


def test_refresh_detects_runtime_regressed() -> None:
    _seed_github_vercel_railway(
        "refresh-runtime",
        vercel_state="ready",
        railway_status="unhealthy",
        commit="abc123def456",
    )
    vercel_payload = {
        "ok": True,
        "project_name": "aethos-web",
        "deployments": {
            "deployments": [
                {"id": "d-new", "state": "ready", "commit": "abc123def456", "branch": "main"},
            ]
        },
        "latest_deployment": {"id": "d-new", "state": "ready", "commit": "abc123def456", "branch": "main"},
        "project": {"details": {"repo_link": "pilotmain/aethos", "name": "aethos-web"}},
    }
    fetch_return = {
        "ok": True,
        "deployments": [{"id": "d-new", "state": "ready", "commit": "abc123def456", "branch": "main"}],
    }
    with _poll_patches(fetch_return=fetch_return, vercel_payload=vercel_payload):
        result = refresh_downstream_evidence_after_rerun(
            session_id="refresh-runtime",
            repository="pilotmain/aethos",
            verification={
                "rerun_outcome": "passed",
                "head_sha": "abc123def456",
                "run_status": "completed",
                "run_conclusion": "success",
            },
        )
    assert result["chain_verdict"] == "runtime_regressed"


def test_refresh_detects_deploy_blocked() -> None:
    _seed_github_vercel_railway("refresh-blocked", vercel_state="error", vercel_deploy_id="d-fail")
    vercel_payload = {
        "ok": True,
        "project_name": "aethos-web",
        "deployments": {
            "deployments": [
                {"id": "d-fail", "state": "error", "commit": "abc123def456", "branch": "main"},
            ]
        },
        "latest_deployment": {"id": "d-fail", "state": "error", "commit": "abc123def456", "branch": "main"},
        "failed_deployment": {"id": "d-fail", "state": "error", "commit": "abc123def456", "branch": "main"},
        "project": {"details": {"repo_link": "pilotmain/aethos", "name": "aethos-web"}},
    }
    fetch_return = {
        "ok": True,
        "deployments": [{"id": "d-fail", "state": "error", "commit": "abc123def456", "branch": "main"}],
    }
    with _poll_patches(fetch_return=fetch_return, vercel_payload=vercel_payload):
        result = refresh_downstream_evidence_after_rerun(
            session_id="refresh-blocked",
            repository="pilotmain/aethos",
            verification={
                "rerun_outcome": "passed",
                "head_sha": "abc123def456",
                "run_status": "completed",
                "run_conclusion": "success",
            },
        )
    assert result["chain_verdict"] == "deploy_blocked"


def test_analyze_deployments_detects_reused_build() -> None:
    analysis = _analyze_deployments_for_rerun(
        vercel_evidence={
            "deployments": {
                "deployments": [{"id": "d-same", "state": "ready", "commit": "abc123"}],
            }
        },
        snapshot={},
        head_sha="abc123",
        before_vercel={"deployment_id": "d-same"},
        rerun_outcome="passed",
    )
    assert analysis["deployment_reused_previous_build"] is True
    assert analysis["new_deployment_created"] is False


def test_update_correlation_persists_refresh_fields() -> None:
    _seed_github_vercel_railway("persist-refresh", vercel_state="ready", vercel_deploy_id="d-old")
    with patch(
        "aethos_core.providers.github.mutations.post_rerun_evidence_refresh._resolve_vercel_token",
        return_value="",
    ), patch(
        "aethos_core.cross_provider_correlation.correlation_store.publish_railway_health_rows",
        return_value=True,
    ):
        update_correlation_after_rerun_verification(
            session_id="persist-refresh",
            repository="pilotmain/aethos",
            verification={
                "source_run_id": 42,
                "rerun_run_id": 99,
                "new_run_detected": True,
                "run_status": "completed",
                "run_conclusion": "success",
                "run_number": 11,
                "head_branch": "main",
                "head_sha": "abc123def456",
                "workflow_name": "CI",
                "rerun_outcome": "passed",
            },
        )
    ctx = get_github_rerun_context("persist-refresh")
    assert ctx is not None
    assert "deployment_chain" in ctx
    assert "chain_verdict" in ctx
    assert "timeline" in ctx


def test_followup_uses_refreshed_chain_verdict() -> None:
    from aethos_core.providers.github.context.github_context_store import save_github_rerun_context

    save_github_rerun_context(
        "followup-refresh",
        {
            "rerun_target_repo": "pilotmain/aethos",
            "rerun_outcome": "passed",
            "evidence_refreshed": True,
            "chain_verdict": "deploy_not_triggered",
            "deployment_chain": {
                "failure_boundary": "unknown",
                "chain_verdict": "deploy_not_triggered",
                "evidence_refreshed": True,
                "no_deploy_triggered": True,
                "timeline": [
                    {"phase": "rerun_completed", "status": "success", "detail": "Outcome: passed"},
                    {"phase": "deploy_observed", "status": "not_triggered", "detail": "No deploy"},
                ],
            },
        },
    )
    reply = compose_github_workflow_rerun_followup_reply(
        "did deployment reach runtime?",
        session_id="followup-refresh",
    )
    assert reply is not None
    body, _, _ = reply
    assert "deploy_not_triggered" in body
    assert "refreshed" in body.lower()
    assert "Timeline" in body
