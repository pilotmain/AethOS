# SPDX-License-Identifier: Apache-2.0
"""Bounded post-rerun deployment polling tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.cross_provider_correlation.correlation_store import (
    clear_store_for_tests,
    publish_github_evidence,
    publish_railway_evidence,
    publish_vercel_evidence,
)
from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests
from aethos_core.providers.github.mutations.post_rerun_evidence_refresh import (
    refresh_downstream_evidence_after_rerun,
)
from aethos_core.providers.github.mutations.post_rerun_poll_config import PostRerunPollConfig
from aethos_core.providers.github.mutations.workflow_rerun_verification import (
    compose_proactive_github_rerun_verification_reply,
    summarize_verification_for_operator,
)


def setup_function() -> None:
    clear_store_for_tests()
    clear_github_context_for_tests()


def _seed(session_id: str, *, commit: str = "abc123def456", vercel_state: str = "ready", railway: str = "healthy") -> None:
    publish_github_evidence(
        session_id,
        {
            "repository": "pilotmain/aethos",
            "branch": {"branch": "main", "sha": commit},
            "commits": {"commits": [{"sha": commit, "message": "fix", "author": "raya"}]},
            "checks": {"ok": True, "failed_count": 0, "checks": []},
            "workflow_diagnostic": {"ok": True, "latest_failed_run": None},
            "workflow_runs": {"ok": True, "runs": []},
        },
    )
    publish_vercel_evidence(
        session_id,
        {
            "project_name": "aethos-web",
            "project": {"details": {"repo_link": "pilotmain/aethos", "name": "aethos-web"}},
            "latest_deployment": {"id": "d-old", "state": vercel_state, "commit": commit, "branch": "main"},
        },
    )
    publish_railway_evidence(
        session_id,
        {"project": "aethos", "service": "aethos-api", "status": railway, "commit_sha": commit},
    )


def _poll_side_effect(*, attempts: list[list[dict]], vercel_payload: dict):
    call = {"i": 0}

    def _fetch(_token, *, project_name, limit=10):
        idx = min(call["i"], len(attempts) - 1)
        call["i"] += 1
        return {"ok": True, "deployments": attempts[idx]}

    def _collect(*_args, **_kwargs):
        return vercel_payload

    return _fetch, _collect


def test_deploy_appears_after_delay() -> None:
    _seed("poll-delay")
    vercel_payload = {
        "ok": True,
        "project_name": "aethos-web",
        "deployments": {"deployments": [{"id": "d-new", "state": "ready", "commit": "abc123def456"}]},
        "latest_deployment": {"id": "d-new", "state": "ready", "commit": "abc123def456"},
        "project": {"details": {"repo_link": "pilotmain/aethos", "name": "aethos-web"}},
    }
    fetch, collect = _poll_side_effect(
        attempts=[[], [{"id": "d-new", "state": "ready", "commit": "abc123def456"}]],
        vercel_payload=vercel_payload,
    )
    cfg = PostRerunPollConfig(deploy_poll_seconds=30, deploy_poll_interval_seconds=1, runtime_settle_seconds=0)
    with patch(
        "aethos_core.providers.github.mutations.post_rerun_evidence_refresh._resolve_vercel_token",
        return_value="token",
    ), patch(
        "aethos_core.providers.vercel.operations.deployments_api.fetch_deployments",
        side_effect=fetch,
    ), patch(
        "aethos_core.providers.vercel.diagnostics.deployment_evidence_collector.collect_vercel_live_evidence",
        side_effect=collect,
    ), patch(
        "aethos_core.providers.github.mutations.post_rerun_evidence_refresh._sleep_seconds",
    ), patch(
        "aethos_core.providers.github.mutations.post_rerun_evidence_refresh.PostRerunPollConfig.from_env",
        return_value=cfg,
    ), patch(
        "aethos_core.cross_provider_correlation.correlation_store.publish_railway_health_rows",
        return_value=True,
    ):
        result = refresh_downstream_evidence_after_rerun(
            session_id="poll-delay",
            repository="pilotmain/aethos",
            verification={"rerun_outcome": "passed", "head_sha": "abc123def456", "run_status": "completed"},
        )
    assert result["chain_verdict"] == "chain_healthy"
    assert result["deployment_chain"]["poll_metadata"]["poll_attempt_count"] >= 2


def test_deploy_never_appears_after_wait() -> None:
    _seed("poll-never", commit="oldcommit111")
    cfg = PostRerunPollConfig(deploy_poll_seconds=20, deploy_poll_interval_seconds=1, runtime_settle_seconds=0)
    with patch(
        "aethos_core.providers.github.mutations.post_rerun_evidence_refresh._resolve_vercel_token",
        return_value="token",
    ), patch(
        "aethos_core.providers.vercel.operations.deployments_api.fetch_deployments",
        return_value={"ok": True, "deployments": [{"id": "d-old", "state": "ready", "commit": "oldcommit111"}]},
    ), patch(
        "aethos_core.providers.github.mutations.post_rerun_evidence_refresh._sleep_seconds",
    ), patch(
        "aethos_core.providers.github.mutations.post_rerun_evidence_refresh.PostRerunPollConfig.from_env",
        return_value=cfg,
    ), patch(
        "aethos_core.cross_provider_correlation.correlation_store.publish_railway_health_rows",
        return_value=True,
    ):
        result = refresh_downstream_evidence_after_rerun(
            session_id="poll-never",
            repository="pilotmain/aethos",
            verification={"rerun_outcome": "passed", "head_sha": "newcommit222", "run_status": "completed"},
        )
    assert result["chain_verdict"] == "deploy_not_triggered_after_wait"


def test_deploy_remains_building() -> None:
    _seed("poll-building")
    cfg = PostRerunPollConfig(deploy_poll_seconds=20, deploy_poll_interval_seconds=1, runtime_settle_seconds=0)
    with patch(
        "aethos_core.providers.github.mutations.post_rerun_evidence_refresh._resolve_vercel_token",
        return_value="token",
    ), patch(
        "aethos_core.providers.vercel.operations.deployments_api.fetch_deployments",
        return_value={"ok": True, "deployments": [{"id": "d-new", "state": "building", "commit": "abc123def456"}]},
    ), patch(
        "aethos_core.providers.github.mutations.post_rerun_evidence_refresh._sleep_seconds",
    ), patch(
        "aethos_core.providers.github.mutations.post_rerun_evidence_refresh.PostRerunPollConfig.from_env",
        return_value=cfg,
    ), patch(
        "aethos_core.cross_provider_correlation.correlation_store.publish_railway_health_rows",
        return_value=True,
    ):
        result = refresh_downstream_evidence_after_rerun(
            session_id="poll-building",
            repository="pilotmain/aethos",
            verification={"rerun_outcome": "passed", "head_sha": "abc123def456", "run_status": "completed"},
        )
    assert result["chain_verdict"] == "deploy_still_pending"
    assert "still pending" in result["chain_summary"].lower()


def test_deploy_fails_after_rerun() -> None:
    _seed("poll-failed", vercel_state="error")
    vercel_payload = {
        "ok": True,
        "project_name": "aethos-web",
        "deployments": {"deployments": [{"id": "d-fail", "state": "error", "commit": "abc123def456"}]},
        "latest_deployment": {"id": "d-fail", "state": "error", "commit": "abc123def456"},
        "failed_deployment": {"id": "d-fail", "state": "error", "commit": "abc123def456"},
        "project": {"details": {"repo_link": "pilotmain/aethos", "name": "aethos-web"}},
    }
    with patch(
        "aethos_core.providers.github.mutations.post_rerun_evidence_refresh._resolve_vercel_token",
        return_value="token",
    ), patch(
        "aethos_core.providers.vercel.operations.deployments_api.fetch_deployments",
        return_value={"ok": True, "deployments": [{"id": "d-fail", "state": "error", "commit": "abc123def456"}]},
    ), patch(
        "aethos_core.providers.vercel.diagnostics.deployment_evidence_collector.collect_vercel_live_evidence",
        return_value=vercel_payload,
    ), patch(
        "aethos_core.providers.github.mutations.post_rerun_evidence_refresh.PostRerunPollConfig.from_env",
        return_value=PostRerunPollConfig(deploy_poll_seconds=10, deploy_poll_interval_seconds=1, runtime_settle_seconds=0),
    ), patch(
        "aethos_core.providers.github.mutations.post_rerun_evidence_refresh._sleep_seconds",
    ), patch(
        "aethos_core.cross_provider_correlation.correlation_store.publish_railway_health_rows",
        return_value=True,
    ):
        result = refresh_downstream_evidence_after_rerun(
            session_id="poll-failed",
            repository="pilotmain/aethos",
            verification={"rerun_outcome": "passed", "head_sha": "abc123def456", "run_status": "completed"},
        )
    assert result["chain_verdict"] == "deploy_blocked"


def test_proactive_verification_reply_includes_chain_verdict() -> None:
    reply = compose_proactive_github_rerun_verification_reply(
        {
            "run_number": 12,
            "rerun_outcome": "passed",
            "chain_verdict": "deploy_blocked",
            "chain_summary": "GitHub workflow rerun **passed**, but refreshed Vercel evidence shows deployment is still blocked — workflow success is not deployment success.",
            "deployment_chain": {
                "failure_boundary": "vercel",
                "chain_verdict": "deploy_blocked",
                "poll_metadata": {"polled": True, "poll_attempt_count": 3, "waited_seconds": 30, "deploy_poll_seconds": 120},
                "timeline": [{"phase": "deploy_poll", "status": "error", "detail": "Attempt 1: deployment failed"}],
            },
        }
    )
    assert "Chain verdict: **deploy_blocked**" in reply
    assert "Timeline:" in reply
    assert "3 poll attempt" in reply
    summary = summarize_verification_for_operator(
        {
            "new_run_detected": True,
            "run_number": 12,
            "rerun_outcome": "passed",
            "chain_verdict": "deploy_blocked",
            "deployment_chain": {"chain_verdict": "deploy_blocked"},
        }
    )
    assert "Chain verdict" in summary
