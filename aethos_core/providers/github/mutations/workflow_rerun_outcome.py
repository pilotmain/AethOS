# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow rerun outcome classification and deployment chain analysis."""

from __future__ import annotations

from typing import Any

RERUN_OUTCOMES = frozenset(
    {
        "passed",
        "failed_again",
        "cancelled",
        "timed_out",
        "partial_success",
        "pending",
        "rerun_not_detected",
    }
)

_TERMINAL_STATUSES = frozenset({"completed", "cancelled", "failure", "failed", "skipped"})


def classify_rerun_outcome(
    *,
    new_run_detected: bool,
    run_status: str = "",
    run_conclusion: str = "",
    jobs: list[dict[str, Any]] | None = None,
    completion_timed_out: bool = False,
) -> str:
    if not new_run_detected:
        return "rerun_not_detected"
    status = str(run_status or "").lower()
    conclusion = str(run_conclusion or "").lower()
    if completion_timed_out and status not in _TERMINAL_STATUSES:
        return "timed_out"
    if status in {"queued", "in_progress", "waiting", "requested", "pending"}:
        return "pending"
    if conclusion == "cancelled" or status == "cancelled":
        return "cancelled"
    if conclusion == "failure" or status in {"failure", "failed"}:
        return "failed_again"
    if conclusion == "success" or (status == "completed" and conclusion in {"", "success", "neutral"}):
        if _has_partial_job_failures(jobs):
            return "partial_success"
        return "passed"
    if conclusion in {"timed_out", "action_required", "stale"}:
        return "failed_again"
    if status == "completed":
        return "passed" if conclusion in {"success", "neutral", ""} else "failed_again"
    return "pending"


def _has_partial_job_failures(jobs: list[dict[str, Any]] | None) -> bool:
    if not jobs:
        return False
    conclusions = {str(job.get("conclusion") or "").lower() for job in jobs if isinstance(job, dict)}
    return "success" in conclusions and "failure" in conclusions


def summarize_failed_jobs(jobs: list[dict[str, Any]] | None) -> dict[str, Any]:
    failed_jobs: list[dict[str, Any]] = []
    likely_job: str | None = None
    likely_step: str | None = None
    for job in jobs or []:
        if not isinstance(job, dict):
            continue
        job_name = str(job.get("name") or "")
        job_conclusion = str(job.get("conclusion") or "").lower()
        failed_steps: list[str] = []
        for step in job.get("steps") or []:
            if not isinstance(step, dict):
                continue
            if str(step.get("conclusion") or "").lower() == "failure":
                step_name = str(step.get("name") or "")
                failed_steps.append(step_name)
                if likely_step is None:
                    likely_job = job_name
                    likely_step = step_name
        if job_conclusion == "failure" or failed_steps:
            failed_jobs.append(
                {
                    "name": job_name,
                    "conclusion": job_conclusion,
                    "failed_steps": failed_steps,
                }
            )
            if likely_job is None and job_name:
                likely_job = job_name
    return {
        "failed_jobs": failed_jobs,
        "failed_job_count": len(failed_jobs),
        "likely_failure_job": likely_job,
        "likely_failure_step": likely_step,
    }


def analyze_rerun_deployment_chain(
    *,
    session_id: str,
    rerun_outcome: str,
) -> dict[str, Any]:
    from aethos_core.cross_provider_correlation.correlation_runtime import build_correlation_state

    state = build_correlation_state(session_id=session_id)
    corr = dict(state.get("cross_provider_correlation") or {})
    boundary = str(corr.get("failure_boundary") or "unknown")
    github_passed = rerun_outcome in {"passed", "partial_success"}
    vercel_project = corr.get("vercel_project")
    railway_service = corr.get("railway_service")

    scenarios: list[str] = []
    if rerun_outcome == "rerun_not_detected":
        scenarios.append("rerun_triggered_nothing")
    elif rerun_outcome in {"failed_again", "cancelled", "timed_out"}:
        scenarios.append("github_workflow_failed")
    elif github_passed and boundary == "vercel":
        scenarios.append("workflow_passed_deploy_failed")
    elif github_passed and boundary == "railway":
        scenarios.append("deploy_succeeded_runtime_unhealthy")
    elif github_passed and boundary == "none":
        scenarios.append("chain_healthy")
    elif github_passed and boundary in {"unknown", "missing"}:
        scenarios.append("workflow_passed_downstream_unverified")
    elif github_passed:
        scenarios.append("workflow_passed_boundary_mixed")

    chain_healthy = github_passed and boundary == "none"
    workflow_only_success = rerun_outcome == "passed"
    return {
        "failure_boundary": boundary,
        "confidence": str(corr.get("confidence") or "low"),
        "conclusion": str(corr.get("conclusion") or ""),
        "vercel_project": vercel_project,
        "railway_service": railway_service,
        "scenarios": scenarios,
        "chain_healthy": chain_healthy,
        "workflow_only_success": workflow_only_success,
        "workflow_passed_deploy_failed": github_passed and boundary == "vercel",
        "deploy_succeeded_runtime_unhealthy": github_passed and boundary == "railway",
        "rerun_triggered_nothing": rerun_outcome == "rerun_not_detected",
    }


def chain_verification_result(*, rerun_outcome: str, deployment_chain: dict[str, Any]) -> str:
    verdict = str(deployment_chain.get("chain_verdict") or "")
    if verdict == "chain_healthy":
        return "healthy"
    if verdict in {"deploy_blocked", "runtime_regressed", "deploy_not_triggered", "deploy_not_triggered_after_wait", "deploy_still_pending", "inconclusive_timeout"}:
        return "inconclusive"
    if rerun_outcome == "rerun_not_detected":
        return "unhealthy"
    if rerun_outcome in {"failed_again", "cancelled"}:
        return "unhealthy"
    if rerun_outcome == "timed_out":
        return "inconclusive"
    if rerun_outcome == "pending":
        return "pending"
    if deployment_chain.get("chain_healthy"):
        return "healthy"
    if rerun_outcome == "passed" and not deployment_chain.get("chain_healthy"):
        return "inconclusive"
    if rerun_outcome == "partial_success":
        return "inconclusive"
    return "inconclusive"


def compose_chain_summary(*, rerun_outcome: str, deployment_chain: dict[str, Any]) -> str:
    verdict = str(deployment_chain.get("chain_verdict") or "")
    if verdict == "chain_healthy":
        return "GitHub rerun passed and refreshed Vercel/Railway evidence shows the full deploy/runtime chain is healthy."
    if verdict == "deploy_blocked":
        return "GitHub workflow rerun **passed**, but refreshed Vercel evidence shows deployment is still blocked — workflow success is not deployment success."
    if verdict == "runtime_regressed":
        return "GitHub and Vercel look healthy after refresh, but Railway runtime is still unhealthy."
    if verdict == "deploy_not_triggered":
        return "GitHub workflow rerun **passed**, but no new Vercel deployment was observed for the rerun commit — deploy may not have been triggered."
    if verdict == "deploy_not_triggered_after_wait":
        return (
            "GitHub workflow rerun **passed**, but no Vercel deployment matched the rerun commit after waiting for downstream propagation."
        )
    if verdict == "deploy_still_pending":
        waited = int(deployment_chain.get("poll_metadata", {}).get("deploy_poll_seconds") or 120)
        return (
            "The GitHub rerun passed, but downstream deployment is still pending.\n"
            f"I waited {waited} seconds and did not see a terminal Vercel deployment yet."
        )
    if verdict == "inconclusive_timeout":
        waited = int(deployment_chain.get("poll_metadata", {}).get("deploy_poll_seconds") or 120)
        return (
            "GitHub workflow rerun **passed**, but downstream Vercel/Railway evidence did not stabilize within the bounded wait window "
            f"({waited}s)."
        )
    if deployment_chain.get("rerun_triggered_nothing"):
        return "No new workflow run was detected after the governed rerun."
    if deployment_chain.get("workflow_passed_deploy_failed"):
        return "GitHub workflow rerun **passed**, but the correlated Vercel deployment is still failing — workflow success is not deployment success."
    if deployment_chain.get("deploy_succeeded_runtime_unhealthy"):
        return "GitHub and Vercel look healthy on the correlated commit, but Railway runtime is still unhealthy."
    if deployment_chain.get("chain_healthy"):
        return "GitHub rerun passed and the correlated Vercel/Railway chain looks healthy."
    if rerun_outcome == "failed_again":
        return "GitHub workflow rerun **failed again** — inspect failed jobs/steps on the rerun run."
    if rerun_outcome == "passed":
        return "GitHub workflow rerun **passed**, but downstream deploy/runtime evidence is not fully verified yet."
    if rerun_outcome == "timed_out":
        return "GitHub workflow rerun was detected but did not reach a terminal state before verification timed out."
    if rerun_outcome == "cancelled":
        return "GitHub workflow rerun was **cancelled** before completion."
    return f"GitHub workflow rerun outcome: **{rerun_outcome}**."
