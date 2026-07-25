# SPDX-License-Identifier: Apache-2.0
"""Automatic downstream evidence refresh after GitHub workflow rerun."""

from __future__ import annotations

import time
from typing import Any

from aethos_core.cross_provider_correlation.commit_identity import commits_match
from aethos_core.providers.github.mutations.post_rerun_poll_config import PostRerunPollConfig
from aethos_core.providers.github.mutations.workflow_rerun_outcome import (
    analyze_rerun_deployment_chain,
    compose_chain_summary,
)

CHAIN_VERDICTS = frozenset(
    {
        "chain_healthy",
        "deploy_blocked",
        "runtime_regressed",
        "deploy_not_triggered",
        "deploy_not_triggered_after_wait",
        "deploy_still_pending",
        "inconclusive",
        "inconclusive_timeout",
    }
)

_TERMINAL_DEPLOY_STATES = frozenset({"ready", "completed", "error", "failed", "canceled", "cancelled"})
_PENDING_DEPLOY_STATES = frozenset({"building", "queued", "initializing", "pending", "deploying", "preparing"})


def refresh_downstream_evidence_after_rerun(
    *,
    session_id: str,
    repository: str,
    verification: dict[str, Any],
) -> dict[str, Any]:
    from aethos_core.cross_provider_correlation.correlation_runtime import build_correlation_state
    from aethos_core.cross_provider_correlation.correlation_store import get_session_snapshot

    rerun_outcome = str(verification.get("rerun_outcome") or "pending")
    head_sha = str(verification.get("head_sha") or "")
    before_snapshot = get_session_snapshot(session_id)
    before_vercel = dict(before_snapshot.get("vercel") or {})
    before_railway = dict(before_snapshot.get("railway") or {})

    refresh_result: dict[str, Any] = {
        "evidence_refreshed": False,
        "vercel_refreshed": False,
        "railway_refreshed": False,
        "refresh_errors": [],
    }

    project_name = _resolve_vercel_project(session_id=session_id, repository=repository, snapshot=before_snapshot)
    vercel_token = _resolve_vercel_token()
    vercel_evidence: dict[str, Any] | None = None
    poll_metadata: dict[str, Any] = {"polled": False}

    github_passed = rerun_outcome in {"passed", "partial_success"}
    if project_name and vercel_token and github_passed:
        poll_metadata = _poll_vercel_deployment_for_rerun(
            token=vercel_token,
            project_name=project_name,
            session_id=session_id,
            head_sha=head_sha,
            before_vercel=before_vercel,
        )
        vercel_evidence = poll_metadata.get("vercel_evidence")
        refresh_result["vercel_refreshed"] = bool((vercel_evidence or {}).get("ok"))
        refresh_result["vercel_project"] = project_name
        refresh_result["poll_metadata"] = poll_metadata
    elif project_name and vercel_token and rerun_outcome in {"failed_again", "pending"}:
        try:
            from aethos_core.providers.vercel.diagnostics.deployment_evidence_collector import (
                collect_vercel_live_evidence,
            )

            vercel_evidence = collect_vercel_live_evidence(
                vercel_token,
                project_name=project_name,
                session_id=session_id,
                operation="live_diagnosis",
            )
            refresh_result["vercel_refreshed"] = bool(vercel_evidence.get("ok"))
            refresh_result["vercel_project"] = project_name
        except Exception as exc:
            refresh_result["refresh_errors"].append(f"vercel: {exc}")
    elif project_name and not vercel_token:
        refresh_result["refresh_errors"].append("vercel: API token not configured")

    if poll_metadata.get("deploy_terminal") and poll_metadata.get("runtime_settle_seconds", 0) > 0:
        _sleep_seconds(int(poll_metadata["runtime_settle_seconds"]))

    try:
        from aethos_core.cross_provider_correlation.correlation_store import publish_railway_health_rows

        published = publish_railway_health_rows(session_id)
        refresh_result["railway_refreshed"] = bool(published)
    except Exception as exc:
        refresh_result["refresh_errors"].append(f"railway: {exc}")

    after_state = build_correlation_state(session_id=session_id)
    after_snapshot = get_session_snapshot(session_id)
    deploy_analysis = _analyze_deployments_for_rerun(
        vercel_evidence=vercel_evidence,
        snapshot=after_snapshot,
        head_sha=head_sha,
        before_vercel=before_vercel,
        rerun_outcome=rerun_outcome,
        poll_metadata=poll_metadata,
    )
    timeline = _build_rerun_timeline(
        verification=verification,
        deploy_analysis=deploy_analysis,
        before_railway=before_railway,
        after_snapshot=after_snapshot,
        poll_metadata=poll_metadata,
    )
    deployment_chain = analyze_rerun_deployment_chain(session_id=session_id, rerun_outcome=rerun_outcome)
    chain_verdict = _classify_chain_verdict(
        rerun_outcome=rerun_outcome,
        deployment_chain=deployment_chain,
        deploy_analysis=deploy_analysis,
        after_state=after_state,
        evidence_refreshed=refresh_result["vercel_refreshed"] or refresh_result["railway_refreshed"],
        poll_metadata=poll_metadata,
    )
    deployment_chain = {
        **deployment_chain,
        **deploy_analysis,
        "chain_verdict": chain_verdict,
        "timeline": timeline,
        "poll_metadata": poll_metadata,
        "evidence_refreshed": refresh_result["vercel_refreshed"] or refresh_result["railway_refreshed"],
        "correlation_state": after_state.get("cross_provider_correlation"),
    }
    refresh_result.update(
        {
            "evidence_refreshed": deployment_chain["evidence_refreshed"],
            "deployment_chain": deployment_chain,
            "chain_verdict": chain_verdict,
            "timeline": timeline,
            "chain_summary": compose_chain_summary(
                rerun_outcome=rerun_outcome,
                deployment_chain=deployment_chain,
            ),
        }
    )
    return refresh_result


def _resolve_vercel_project(
    *,
    session_id: str,
    repository: str,
    snapshot: dict[str, Any],
) -> str:
    vercel = dict(snapshot.get("vercel") or {})
    if vercel.get("project"):
        return str(vercel["project"])
    raw_vercel = dict((snapshot.get("raw") or {}).get("vercel") or {})
    if raw_vercel.get("project_name"):
        return str(raw_vercel["project_name"])
    from aethos_core.cross_provider_correlation.correlation_runtime import build_correlation_state

    state = build_correlation_state(session_id=session_id)
    corr = dict(state.get("cross_provider_correlation") or {})
    if corr.get("vercel_project"):
        return str(corr["vercel_project"])
    try:
        from aethos_core.cross_provider_correlation.evidence_linker import _load_bindings

        for binding in _load_bindings():
            if binding.github_repo and repository and binding.vercel_project:
                repo_key = repository.lower()
                if binding.github_repo.lower() in repo_key or repo_key.endswith(binding.github_repo.split("/")[-1].lower()):
                    return str(binding.vercel_project)
    except Exception:
        pass
    return ""


def _resolve_vercel_token() -> str:
    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    auth = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
    credential_id = str(auth.get("credential_id") or "")
    if not credential_id:
        return ""
    return VercelAuthAdapter().get_api_token(credential_id) or ""


def _poll_vercel_deployment_for_rerun(
    *,
    token: str,
    project_name: str,
    session_id: str,
    head_sha: str,
    before_vercel: dict[str, Any],
    config: PostRerunPollConfig | None = None,
) -> dict[str, Any]:
    from aethos_core.providers.vercel.operations.deployments_api import fetch_deployments

    cfg = config or PostRerunPollConfig.from_env()
    started_at = time.time()
    deadline = started_at + cfg.deploy_poll_seconds
    poll_attempts: list[dict[str, Any]] = []
    matched: dict[str, Any] | None = None
    matched_state = ""
    deployments: list[dict[str, Any]] = []
    vercel_evidence: dict[str, Any] | None = None
    deploy_terminal = False
    deploy_still_pending = False
    deploy_not_seen = True

    while time.time() <= deadline:
        attempt_started = time.time()
        try:
            payload = fetch_deployments(token, project_name=project_name, limit=10)
        except Exception as exc:
            poll_attempts.append(
                {
                    "attempt": len(poll_attempts) + 1,
                    "status": "error",
                    "detail": str(exc),
                }
            )
            _sleep_seconds(cfg.deploy_poll_interval_seconds)
            continue

        deployments = list(payload.get("deployments") or [])
        matched = _find_deployment_for_commit(deployments, head_sha)
        matched_state = str((matched or {}).get("state") or "").lower()
        poll_attempts.append(
            {
                "attempt": len(poll_attempts) + 1,
                "status": matched_state or ("no_match" if not matched else "unknown"),
                "detail": (
                    f"Deployment `{str((matched or {}).get('id') or '')[:12]}`"
                    if matched
                    else "No deployment matched rerun commit yet."
                ),
            }
        )
        if matched:
            deploy_not_seen = False
            if _is_terminal_deploy_state(matched_state):
                deploy_terminal = True
                break
            deploy_still_pending = True
        elif time.time() + cfg.deploy_poll_interval_seconds > deadline:
            break
        _sleep_seconds(cfg.deploy_poll_interval_seconds)

    waited_seconds = min(cfg.deploy_poll_seconds, max(0, int(time.time() - started_at)))

    if matched and deploy_terminal:
        try:
            from aethos_core.providers.vercel.diagnostics.deployment_evidence_collector import (
                collect_vercel_live_evidence,
            )

            vercel_evidence = collect_vercel_live_evidence(
                token,
                project_name=project_name,
                session_id=session_id,
                operation="live_diagnosis",
            )
        except Exception as exc:
            poll_attempts.append({"attempt": len(poll_attempts) + 1, "status": "ingest_error", "detail": str(exc)})
    elif not matched and deployments:
        deploy_not_seen = True
    elif matched and not deploy_terminal:
        deploy_still_pending = True

    return {
        "polled": True,
        "poll_attempts": poll_attempts,
        "poll_attempt_count": len(poll_attempts),
        "waited_seconds": waited_seconds,
        "deploy_poll_seconds": cfg.deploy_poll_seconds,
        "deploy_poll_interval_seconds": cfg.deploy_poll_interval_seconds,
        "runtime_settle_seconds": cfg.runtime_settle_seconds if deploy_terminal else 0,
        "matched_deployment": matched,
        "matched_deployment_state": matched_state or None,
        "deploy_terminal": deploy_terminal,
        "deploy_still_pending": deploy_still_pending and not deploy_terminal,
        "deploy_not_seen": deploy_not_seen and not matched,
        "vercel_evidence": vercel_evidence,
        "deployments": deployments,
        "before_deploy_id": str(before_vercel.get("deployment_id") or ""),
    }


def _is_terminal_deploy_state(state: str) -> bool:
    normalized = str(state or "").lower()
    if normalized in _TERMINAL_DEPLOY_STATES:
        return True
    if normalized in _PENDING_DEPLOY_STATES:
        return False
    return normalized not in {"", "unknown"}


def _sleep_seconds(seconds: int) -> None:
    if seconds > 0:
        time.sleep(seconds)


def _analyze_deployments_for_rerun(
    *,
    vercel_evidence: dict[str, Any] | None,
    snapshot: dict[str, Any],
    head_sha: str,
    before_vercel: dict[str, Any],
    rerun_outcome: str,
    poll_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    poll_metadata = dict(poll_metadata or {})
    deployments = list((vercel_evidence or {}).get("deployments", {}).get("deployments") or [])
    if not deployments and poll_metadata.get("deployments"):
        deployments = list(poll_metadata.get("deployments") or [])
    if not deployments:
        raw = dict((snapshot.get("raw") or {}).get("vercel") or {})
        deployments = list((raw.get("deployments") or {}).get("deployments") or [])

    matched = poll_metadata.get("matched_deployment")
    if not matched:
        matched = _find_deployment_for_commit(deployments, head_sha)
    matched = dict(matched or {})
    latest = deployments[0] if deployments else None
    before_deploy_id = str(before_vercel.get("deployment_id") or "")
    matched_id = str((matched or {}).get("id") or "")
    matched_state = str((matched or {}).get("state") or "").lower()

    new_deployment_created = bool(
        matched
        and matched_id
        and matched_id != before_deploy_id
        and commits_match(str(matched.get("commit") or ""), head_sha)
    )
    deployment_reused = bool(
        matched
        and matched_id
        and matched_id == before_deploy_id
        and commits_match(str(matched.get("commit") or ""), head_sha)
    )
    github_passed = rerun_outcome in {"passed", "partial_success"}
    no_deploy_triggered = bool(
        github_passed
        and not matched
        and not commits_match(str((latest or {}).get("commit") or ""), head_sha)
    )
    if poll_metadata.get("polled"):
        no_deploy_triggered = bool(poll_metadata.get("deploy_not_seen"))

    return {
        "matched_deployment": matched or None,
        "latest_deployment": latest,
        "new_deployment_created": new_deployment_created,
        "deployment_reused_previous_build": deployment_reused,
        "no_deploy_triggered": no_deploy_triggered,
        "matched_deployment_state": matched_state or None,
        "matched_deployment_id": matched_id or None,
        "deploy_still_pending": bool(poll_metadata.get("deploy_still_pending")),
    }


def _find_deployment_for_commit(deployments: list[dict[str, Any]], commit_sha: str) -> dict[str, Any] | None:
    if not commit_sha:
        return None
    for row in deployments:
        if isinstance(row, dict) and commits_match(str(row.get("commit") or ""), commit_sha):
            return row
    return None


def _classify_chain_verdict(
    *,
    rerun_outcome: str,
    deployment_chain: dict[str, Any],
    deploy_analysis: dict[str, Any],
    after_state: dict[str, Any],
    evidence_refreshed: bool,
    poll_metadata: dict[str, Any] | None = None,
) -> str:
    poll_metadata = dict(poll_metadata or {})
    if rerun_outcome in {"rerun_not_detected", "cancelled", "timed_out"}:
        return "inconclusive"
    if rerun_outcome == "failed_again":
        return "deploy_blocked" if deployment_chain.get("workflow_passed_deploy_failed") else "inconclusive"

    boundary = str(deployment_chain.get("failure_boundary") or "unknown")
    github_passed = rerun_outcome in {"passed", "partial_success"}

    if poll_metadata.get("polled"):
        if deploy_analysis.get("deploy_still_pending"):
            return "deploy_still_pending"
        if deploy_analysis.get("no_deploy_triggered"):
            return "deploy_not_triggered_after_wait"
        if not evidence_refreshed and github_passed:
            return "inconclusive_timeout"
    elif not evidence_refreshed and github_passed:
        return "inconclusive"

    if deploy_analysis.get("no_deploy_triggered") and not poll_metadata.get("polled"):
        return "deploy_not_triggered"
    if github_passed and boundary == "vercel":
        return "deploy_blocked"
    if github_passed and boundary == "railway":
        return "runtime_regressed"
    if deployment_chain.get("chain_healthy"):
        return "chain_healthy"
    if github_passed and deploy_analysis.get("matched_deployment_state") in {"error", "failed", "canceled", "cancelled"}:
        return "deploy_blocked"
    if poll_metadata.get("polled") and github_passed:
        return "inconclusive_timeout"
    return "inconclusive"


def _build_rerun_timeline(
    *,
    verification: dict[str, Any],
    deploy_analysis: dict[str, Any],
    before_railway: dict[str, Any],
    after_snapshot: dict[str, Any],
    poll_metadata: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    poll_metadata = dict(poll_metadata or {})
    timeline: list[dict[str, str]] = []
    if verification.get("created_at") or verification.get("rerun_run_id"):
        timeline.append(
            {
                "phase": "rerun_detected",
                "status": str(verification.get("run_status") or "detected"),
                "detail": f"Run #{verification.get('run_number') or verification.get('rerun_run_id') or '—'}",
            }
        )
    if str(verification.get("run_status") or "").lower() == "completed":
        timeline.append(
            {
                "phase": "rerun_completed",
                "status": str(verification.get("run_conclusion") or verification.get("rerun_outcome") or "unknown"),
                "detail": f"Outcome: {verification.get('rerun_outcome') or '—'}",
            }
        )
    for attempt in poll_metadata.get("poll_attempts") or []:
        timeline.append(
            {
                "phase": "deploy_poll",
                "status": str(attempt.get("status") or "unknown"),
                "detail": f"Attempt {attempt.get('attempt')}: {attempt.get('detail') or '—'}",
            }
        )
    if poll_metadata.get("polled"):
        timeline.append(
            {
                "phase": "deploy_wait",
                "status": "completed" if poll_metadata.get("deploy_terminal") else "timed_out",
                "detail": (
                    f"Waited {poll_metadata.get('waited_seconds', poll_metadata.get('deploy_poll_seconds', 0))}s "
                    f"over {poll_metadata.get('poll_attempt_count', 0)} poll attempt(s)."
                ),
            }
        )
    matched = dict(deploy_analysis.get("matched_deployment") or {})
    if matched:
        timeline.append(
            {
                "phase": "deploy_observed",
                "status": str(matched.get("state") or "unknown"),
                "detail": f"Deployment `{str(matched.get('id') or '')[:12]}` on commit `{str(matched.get('commit') or '')[:12]}`",
            }
        )
    elif deploy_analysis.get("deploy_still_pending"):
        timeline.append(
            {
                "phase": "deploy_observed",
                "status": "pending",
                "detail": "Vercel deployment matched the rerun commit but did not reach a terminal state within the wait window.",
            }
        )
    elif deploy_analysis.get("no_deploy_triggered"):
        timeline.append(
            {
                "phase": "deploy_observed",
                "status": "not_triggered",
                "detail": "No Vercel deployment matched the rerun commit after refresh.",
            }
        )
    after_railway = dict(after_snapshot.get("railway") or {})
    railway_status = str(after_railway.get("status") or "unknown")
    if after_railway:
        before_status = str(before_railway.get("status") or "unknown")
        detail = f"Runtime status: **{railway_status}**"
        if before_status != railway_status and before_status != "unknown":
            detail = f"Runtime changed `{before_status}` → `{railway_status}`"
        timeline.append({"phase": "runtime_checked", "status": railway_status, "detail": detail})
    return timeline
