# SPDX-License-Identifier: Apache-2.0
"""Poll GitHub workflow runs after rerun — verification only (repo-scoped)."""

from __future__ import annotations

import time
from typing import Any

from aethos_core.operations.mutations.failures import RUN_NOT_DETECTED, VERIFICATION_TIMEOUT, classify_verification_failure
from aethos_core.operations.mutations.retry import RetryAttempt, exponential_backoff_ms
from aethos_core.providers.github.mutations.workflow_rerun_outcome import classify_rerun_outcome, summarize_failed_jobs
from aethos_core.providers.github.operations.workflow_diagnostics_api import fetch_run_jobs
from aethos_core.providers.github.operations.workflow_runs_api import fetch_workflow_runs


def _parse_ts(value: Any) -> float:
    if not value:
        return 0.0
    raw = str(value)
    try:
        from datetime import datetime

        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw).timestamp()
    except ValueError:
        return 0.0


def _match_new_run(
    runs: list[dict[str, Any]],
    *,
    source_run_id: str | None,
    source_created_at: Any,
    workflow_id: Any,
    source_run_number: int | None,
) -> dict[str, Any] | None:
    source_ts = _parse_ts(source_created_at)
    wf_id = str(workflow_id) if workflow_id is not None else None

    candidates: list[dict[str, Any]] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        run_id = str(run.get("id") or "")
        if source_run_id and run_id == source_run_id:
            continue
        run_wf = run.get("workflow_id")
        if wf_id and run_wf is not None and str(run_wf) != wf_id:
            continue
        run_ts = _parse_ts(run.get("created_at"))
        run_number = run.get("run_number")
        status = str(run.get("status") or "").lower()
        newer_ts = source_ts == 0 or run_ts > source_ts
        newer_number = (
            source_run_number is not None
            and isinstance(run_number, int)
            and run_number > source_run_number
        )
        active = status in ("queued", "in_progress", "waiting", "requested", "pending")
        if newer_ts or newer_number or active:
            candidates.append(run)

    if not candidates:
        return None
    candidates.sort(key=lambda r: (_parse_ts(r.get("created_at")), int(r.get("run_number") or 0)), reverse=True)
    return candidates[0]


def _find_run_by_id(runs: list[dict[str, Any]], run_id: str | int | None) -> dict[str, Any] | None:
    target = str(run_id or "")
    if not target:
        return None
    for run in runs:
        if isinstance(run, dict) and str(run.get("id") or "") == target:
            return run
    return None


def _poll_run_to_completion(
    token: str,
    *,
    repository: str,
    run_id: str | int,
    max_attempts: int = 8,
) -> tuple[dict[str, Any], bool, list[dict[str, Any]]]:
    retries: list[dict[str, Any]] = []
    owner, repo = repository.split("/", 1)
    latest = dict()
    timed_out = False
    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            delay = exponential_backoff_ms(attempt)
            retries.append(
                RetryAttempt(attempt=attempt, reason="rerun_completion_poll", delay_ms=delay).to_dict()
            )
            time.sleep(delay / 1000.0)
        payload = fetch_workflow_runs(token, repository=repository, limit=20)
        if not payload.get("ok"):
            continue
        matched = _find_run_by_id(payload.get("runs") or [], run_id)
        if not matched:
            continue
        latest = matched
        status = str(matched.get("status") or "").lower()
        if status in {"completed", "cancelled"}:
            return latest, False, retries
    timed_out = bool(latest) and str(latest.get("status") or "").lower() not in {"completed", "cancelled"}
    return latest, timed_out, retries


def _attach_job_summary(token: str, *, repository: str, run_id: str | int) -> dict[str, Any]:
    owner, repo = repository.split("/", 1)
    jobs_payload = fetch_run_jobs(token, owner=owner, repo=repo, run_id=run_id)
    jobs = list(jobs_payload.get("jobs") or []) if jobs_payload.get("ok") else []
    summary = summarize_failed_jobs(jobs)
    summary["jobs"] = jobs
    return summary


def verify_github_workflow_rerun(
    token: str,
    *,
    repository: str,
    source_run_id: str | int | None,
    workflow_id: str | int | None = None,
    source_created_at: Any = None,
    source_run_number: int | None = None,
    max_attempts: int = 5,
    completion_poll_attempts: int = 8,
    stabilization_wait_ms: int = 4000,
) -> dict[str, Any]:
    retries: list[dict[str, Any]] = []
    source_id = str(source_run_id) if source_run_id is not None else None
    wf_id = workflow_id

    if stabilization_wait_ms > 0:
        retries.append(
            RetryAttempt(
                attempt=0,
                reason="stabilization_wait",
                delay_ms=stabilization_wait_ms,
            ).to_dict()
        )
        time.sleep(stabilization_wait_ms / 1000.0)

    last_payload_error: str | None = None

    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            delay = exponential_backoff_ms(attempt)
            retries.append(
                RetryAttempt(attempt=attempt, reason="provider_eventual_consistency", delay_ms=delay).to_dict()
            )
            time.sleep(delay / 1000.0)

        payload = fetch_workflow_runs(token, repository=repository, limit=20)

        if not payload.get("ok"):
            last_payload_error = str(payload.get("error") or "workflow runs fetch failed")
            if attempt == max_attempts:
                return _failure_payload(
                    retries=retries,
                    attempt=attempt,
                    failure_classification=VERIFICATION_TIMEOUT
                    if "timeout" in last_payload_error.lower()
                    else classify_verification_failure(reason=last_payload_error),
                    last_payload_error=last_payload_error,
                    source_run_id=source_id,
                )
            continue

        matched = _match_new_run(
            payload.get("runs") or [],
            source_run_id=source_id,
            source_created_at=source_created_at,
            workflow_id=wf_id,
            source_run_number=source_run_number,
        )
        if not matched:
            continue

        new_run_id = matched.get("id")
        completed_run, completion_timed_out, completion_retries = _poll_run_to_completion(
            token,
            repository=repository,
            run_id=new_run_id,
            max_attempts=completion_poll_attempts,
        )
        retries.extend(completion_retries)
        run = completed_run or matched
        status = str(run.get("status") or "").lower()
        conclusion = str(run.get("conclusion") or "").lower()
        job_summary = _attach_job_summary(token, repository=repository, run_id=new_run_id)
        jobs = list(job_summary.get("jobs") or [])
        rerun_outcome = classify_rerun_outcome(
            new_run_detected=True,
            run_status=status,
            run_conclusion=conclusion,
            jobs=jobs,
            completion_timed_out=completion_timed_out,
        )
        pending = rerun_outcome == "pending" or status in ("queued", "in_progress", "waiting", "requested", "pending")
        healthy = rerun_outcome == "passed"
        return {
            "ok": True,
            "verification_result": "healthy" if healthy else ("pending" if pending else "inconclusive"),
            "source_run_id": source_id,
            "new_run_id": new_run_id,
            "rerun_run_id": new_run_id,
            "new_run_detected": True,
            "run_status": status,
            "run_conclusion": conclusion,
            "run_number": run.get("run_number"),
            "workflow_id": run.get("workflow_id") or wf_id,
            "workflow_name": run.get("name"),
            "created_at": run.get("created_at"),
            "head_branch": run.get("head_branch"),
            "head_sha": run.get("head_sha"),
            "rerun_outcome": rerun_outcome,
            "completion_timed_out": completion_timed_out,
            "failed_jobs": job_summary.get("failed_jobs"),
            "failed_job_count": job_summary.get("failed_job_count"),
            "likely_failure_job": job_summary.get("likely_failure_job"),
            "likely_failure_step": job_summary.get("likely_failure_step"),
            "retries": retries,
            "verification_attempts": attempt,
        }

    return _failure_payload(
        retries=retries,
        attempt=max_attempts,
        failure_classification=VERIFICATION_TIMEOUT if max_attempts >= 5 else RUN_NOT_DETECTED,
        source_run_id=source_id,
    )


def _failure_payload(
    *,
    retries: list[dict[str, Any]],
    attempt: int,
    failure_classification: str,
    source_run_id: str | None = None,
    last_payload_error: str | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "verification_result": "unhealthy",
        "failure_type": classify_verification_failure(reason=last_payload_error or failure_classification),
        "failure_classification": failure_classification,
        "source_run_id": source_run_id,
        "rerun_outcome": "rerun_not_detected",
        "retries": retries,
        "verification_attempts": attempt,
        "new_run_detected": False,
        "detail": last_payload_error or "No new workflow run detected after rerun.",
    }
